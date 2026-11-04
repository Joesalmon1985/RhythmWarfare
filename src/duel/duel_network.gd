extends Node
## Local wifi link for the wizard duel (autoload `DuelNetwork`). One phone hosts, one joins; the two talk over Godot's ENet transport
## on the local network, with plain JSON messages sent through SceneMultiplayer.send_bytes (so no node paths have to match between
## the phones, and the link survives scene changes). A host also shouts "a game is here" by UDP broadcast every second so that a
## joining phone can list nearby games without typing an address; typing the host's address always works as well.
##
## Messages the scenes use ({"t": type, ...}, delivered in order through drain()):
##   hello {name, v}       exchanged on connect (handled here; sets opp_name)
##   ready {on}            lobby: this wizard is ready
##   start {}              host -> client: both go to the duel scene
##   loaded {}             duel scene: this phone has finished loading
##   go {}                 host -> client: the countdown starts now (the host starts it half a round trip later, so both begin together)
##   res {...}             one phrase result (DuelEngine's result)
##   rematch {}            asks for another duel
##   bye {}                leaving
##   closed {why}          made here when the link ends (left, lost, failed)

signal changed

const PROTOCOL := 1
const BEACON_EVERY_S := 1.0
const PING_EVERY_S := 1.0
const SILENCE_LIMIT_S := 7.0
const GAME_TTL_S := 4.0

enum State { IDLE, HOSTING, JOINING, CONNECTED, CLOSED }

var state := State.IDLE
var role := ""  # "host" | "join" | ""
var my_name := "Wizard"
var opp_name := ""
var rtt_ms := 0.0
var last_error := ""
var closed_reason := ""
var games: Dictionary = {}  # "address:port" -> {name, address, port, seen}
var browsing := false
var round_no := 1  # which duel of this link (a rematch makes it 2): messages of another round are ignored

var _peer: ENetMultiplayerPeer
var _opp_id := 0
var _inbox: Array = []
var _beacon: PacketPeerUDP
var _listener: PacketPeerUDP
var _beacon_t := 0.0
var _ping_t := 0.0
var _last_heard := 0.0
var _port := 24710
var _discovery_port := 24711
var _hello_seen := false


func _ready() -> void:
	set_process(true)
	var rules := DuelRules.load_default()
	if rules.errors.is_empty():
		_port = int(rules.cfg["port"])
		_discovery_port = int(rules.cfg["discovery_port"])
	var sm := multiplayer as SceneMultiplayer
	sm.peer_packet.connect(_on_packet)
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_to_server)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)


# --- public ---------------------------------------------------------------------------------------------------------------------

## This phone's private network addresses (the ones a friend on the same wifi can reach), for showing on the host screen.
static func local_addresses() -> PackedStringArray:
	var out := PackedStringArray()
	for a in IP.get_local_addresses():
		var s := str(a)
		if s.count(".") != 3 or s.begins_with("127.") or s.begins_with("169.254."):
			continue
		var parts := s.split(".")
		var p0 := int(parts[0])
		var p1 := int(parts[1])
		if p0 == 10 or (p0 == 192 and p1 == 168) or (p0 == 172 and p1 >= 16 and p1 <= 31):
			out.append(s)
	return out


func port() -> int:
	return _port


func is_connected_to_opponent() -> bool:
	return state == State.CONNECTED


## Start a game others can find. Returns OK or the engine's error; `last_error` says it in words.
func host_game(p_name: String, p_port: int = -1) -> Error:
	close("")
	if p_port > 0:
		_port = p_port
	my_name = p_name
	_peer = ENetMultiplayerPeer.new()
	var err := _peer.create_server(_port, 1)
	if err != OK:
		last_error = "Could not open port %d (%s). Is another duel window already hosting?" % [_port, error_string(err)]
		_peer = null
		return err
	multiplayer.multiplayer_peer = _peer
	role = "host"
	state = State.HOSTING
	last_error = ""
	closed_reason = ""
	_beacon = PacketPeerUDP.new()
	_beacon.set_broadcast_enabled(true)
	_beacon_t = 0.0
	_last_heard = _now()
	changed.emit()
	return OK


## Join the host at `address`.
func join_game(address: String, p_name: String, p_port: int = -1) -> Error:
	close("")
	if p_port > 0:
		_port = p_port
	my_name = p_name
	_peer = ENetMultiplayerPeer.new()
	var err := _peer.create_client(address.strip_edges(), _port)
	if err != OK:
		last_error = "Could not reach %s (%s)." % [address, error_string(err)]
		_peer = null
		return err
	multiplayer.multiplayer_peer = _peer
	role = "join"
	state = State.JOINING
	last_error = ""
	closed_reason = ""
	_last_heard = _now()
	changed.emit()
	return OK


## Listen for hosts on this wifi.
func start_browsing() -> Error:
	if browsing:
		return OK
	_listener = PacketPeerUDP.new()
	var err := _listener.bind(_discovery_port)
	if err != OK:
		last_error = "Cannot listen for nearby games (%s). Type the host's address instead." % error_string(err)
		_listener = null
		return err
	browsing = true
	games.clear()
	return OK


func stop_browsing() -> void:
	if _listener != null:
		_listener.close()
	_listener = null
	browsing = false
	games.clear()


## Sends a message to the opponent (reliable, in order). Returns false when nobody is there.
func send(msg: Dictionary) -> bool:
	if state != State.CONNECTED and not (state == State.HOSTING and _opp_id != 0) and not (state == State.JOINING and _opp_id != 0):
		return false
	if _opp_id == 0:
		return false
	var bytes := JSON.stringify(msg).to_utf8_buffer()
	return (multiplayer as SceneMultiplayer).send_bytes(bytes, _opp_id, MultiplayerPeer.TRANSFER_MODE_RELIABLE, 0) == OK


## Messages that arrived since the last call, oldest first.
func drain() -> Array:
	var out := _inbox
	_inbox = []
	return out


## Half a round trip in seconds, for starting both countdowns together.
func one_way_s() -> float:
	return rtt_ms / 2000.0


func close(why: String = "left") -> void:
	if _peer != null:
		if state == State.CONNECTED and why != "":
			send({"t": "bye"})
		_peer.close()
	_peer = null
	if multiplayer.multiplayer_peer != null and not (multiplayer.multiplayer_peer is OfflineMultiplayerPeer):
		multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	if _beacon != null:
		_beacon.close()
	_beacon = null
	_opp_id = 0
	_hello_seen = false
	opp_name = ""
	role = ""
	rtt_ms = 0.0
	round_no = 1
	state = State.IDLE
	_inbox = []
	changed.emit()


# --- frame ----------------------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if state == State.HOSTING and _beacon != null:
		_beacon_t -= delta
		if _beacon_t <= 0.0:
			_beacon_t = BEACON_EVERY_S
			_send_beacon()
	if browsing and _listener != null:
		while _listener.get_available_packet_count() > 0:
			var from := _listener.get_packet_ip()
			var pkt := _listener.get_packet()
			var v: Variant = _parse(pkt)
			if typeof(v) == TYPE_DICTIONARY and str(v.get("rw", "")) == "duel" and int(v.get("v", 0)) == PROTOCOL:
				var key := "%s:%d" % [from, int(v.get("port", _port))]
				games[key] = {"name": str(v.get("name", "Wizard")), "address": from, "port": int(v.get("port", _port)), "seen": _now()}
				changed.emit()
		var stale: Array = []
		for k in games:
			if _now() - float(games[k]["seen"]) > GAME_TTL_S:
				stale.append(k)
		for k in stale:
			games.erase(k)
		if not stale.is_empty():
			changed.emit()
	if state == State.CONNECTED:
		_ping_t -= delta
		if _ping_t <= 0.0:
			_ping_t = PING_EVERY_S
			send({"t": "ping", "s": Time.get_ticks_usec()})
		if _now() - _last_heard > SILENCE_LIMIT_S:
			_lost("lost")


func _send_beacon() -> void:
	var msg := JSON.stringify({"rw": "duel", "v": PROTOCOL, "name": my_name, "port": _port}).to_utf8_buffer()
	var targets := PackedStringArray(["255.255.255.255", "127.0.0.1"])
	for a in local_addresses():
		var parts := a.split(".")
		targets.append("%s.%s.%s.255" % [parts[0], parts[1], parts[2]])
	for t in targets:
		_beacon.set_dest_address(t, _discovery_port)
		_beacon.put_packet(msg)


## JSON from a packet, or null when it is not JSON (a stray packet is ignored, not an error).
func _parse(bytes: PackedByteArray) -> Variant:
	var j := JSON.new()
	if j.parse(bytes.get_string_from_utf8()) != OK:
		return null
	return j.data


func _now() -> float:
	return float(Time.get_ticks_msec()) / 1000.0


# --- transport events -------------------------------------------------------------------------------------------------------------

func _on_peer_connected(id: int) -> void:
	if role != "host":
		return
	if _opp_id != 0:
		return
	_opp_id = id
	send({"t": "hello", "name": my_name, "v": PROTOCOL})


func _on_connected_to_server() -> void:
	_opp_id = 1
	state = State.JOINING
	send({"t": "hello", "name": my_name, "v": PROTOCOL})


func _on_connection_failed() -> void:
	last_error = "Could not connect. Check that both phones are on the same wifi and the host is waiting."
	_lost("failed")


func _on_peer_disconnected(id: int) -> void:
	if id == _opp_id:
		_lost("left")


func _on_server_disconnected() -> void:
	_lost("left")


func _lost(why: String) -> void:
	if state == State.CLOSED or state == State.IDLE:
		return
	var had_game := state == State.CONNECTED
	if _peer != null:
		_peer.close()
	_peer = null
	if multiplayer.multiplayer_peer != null and not (multiplayer.multiplayer_peer is OfflineMultiplayerPeer):
		multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	if _beacon != null:
		_beacon.close()
	_beacon = null
	_opp_id = 0
	state = State.CLOSED
	closed_reason = why
	_inbox.append({"t": "closed", "why": why, "had_game": had_game})
	changed.emit()


func _on_packet(_id: int, bytes: PackedByteArray) -> void:
	var v: Variant = _parse(bytes)
	if typeof(v) != TYPE_DICTIONARY:
		return
	var msg: Dictionary = v
	_last_heard = _now()
	match str(msg.get("t", "")):
		"hello":
			if int(msg.get("v", 0)) != PROTOCOL:
				last_error = "The other phone runs a different version of the game."
				send({"t": "bye"})
				_lost("version")
				return
			opp_name = str(msg.get("name", "Wizard"))
			_hello_seen = true
			state = State.CONNECTED
			_ping_t = 0.0
			changed.emit()
		"ping":
			send({"t": "pong", "s": msg.get("s", 0)})
		"pong":
			var sample := float(Time.get_ticks_usec() - int(msg.get("s", 0))) / 1000.0
			rtt_ms = sample if rtt_ms <= 0.0 else lerpf(rtt_ms, sample, 0.3)
		"bye":
			_lost("left")
		_:
			_inbox.append(msg)
