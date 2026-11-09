using System.Collections.Generic;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Tiny procedural mesh builder for the bedsit clutter (boxes, tapered cylinders, ellipsoids) with a flat colour per part
    /// stored in vertex colours, so each prop is ONE mesh / draw call and needs no texture. Metres, pivot chosen by the caller.
    /// </summary>
    public sealed class PropMesh
    {
        readonly List<Vector3> _v = new List<Vector3>();
        readonly List<Vector3> _n = new List<Vector3>();
        readonly List<Color32> _c = new List<Color32>();
        readonly List<int> _t = new List<int>();

        void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 n, Color32 col)
        {
            int i = _v.Count;
            _v.Add(a); _v.Add(b); _v.Add(c); _v.Add(d);
            for (int k = 0; k < 4; k++) { _n.Add(n); _c.Add(col); }
            if (Vector3.Dot(Vector3.Cross(b - a, c - a), n) >= 0f) { _t.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 }); }
            else { _t.AddRange(new[] { i, i + 2, i + 1, i, i + 3, i + 2 }); }
        }

        public PropMesh Box(Vector3 centre, Vector3 size, Vector3 euler, Color col)
        {
            var q = Quaternion.Euler(euler); var h = size * 0.5f; Color32 c32 = col;
            Vector3 P(float x, float y, float z) => centre + q * new Vector3(x * h.x, y * h.y, z * h.z);
            Vector3 N(float x, float y, float z) => q * new Vector3(x, y, z);
            Quad(P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1), N(1, 0, 0), c32);
            Quad(P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1), P(-1, -1, -1), N(-1, 0, 0), c32);
            Quad(P(-1, 1, -1), P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), N(0, 1, 0), c32);
            Quad(P(-1, -1, 1), P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), N(0, -1, 0), c32);
            Quad(P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), N(0, 0, 1), c32);
            Quad(P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1), N(0, 0, -1), c32);
            return this;
        }

        /// <summary>Cylinder (or cone frustum when topRadius differs) standing on its base centre.</summary>
        public PropMesh Cyl(Vector3 baseCentre, float radius, float height, Vector3 euler, Color col, float topRadius = -1f, int seg = 12)
        {
            if (topRadius < 0f) topRadius = radius;
            var q = Quaternion.Euler(euler); Color32 c32 = col;
            Vector3 B(float a, float r) => baseCentre + q * new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r);
            Vector3 T(float a, float r) => baseCentre + q * new Vector3(Mathf.Cos(a) * r, height, Mathf.Sin(a) * r);
            for (int i = 0; i < seg; i++)
            {
                float a0 = i * Mathf.PI * 2f / seg, a1 = (i + 1) * Mathf.PI * 2f / seg, am = (a0 + a1) * 0.5f;
                var n = q * new Vector3(Mathf.Cos(am), (radius - topRadius) / Mathf.Max(height, 0.001f), Mathf.Sin(am)).normalized;
                Quad(B(a0, radius), B(a1, radius), T(a1, topRadius), T(a0, topRadius), n, c32);
                // caps (triangle fans as degenerate quads)
                Quad(T(a0, topRadius), T(a1, topRadius), baseCentre + q * new Vector3(0, height, 0), baseCentre + q * new Vector3(0, height, 0), q * Vector3.up, c32);
                Quad(B(a1, radius), B(a0, radius), baseCentre, baseCentre, q * Vector3.down, c32);
            }
            return this;
        }

        public PropMesh Blob(Vector3 centre, Vector3 radii, Vector3 euler, Color col, int stacks = 6, int slices = 10)
        {
            var q = Quaternion.Euler(euler); Color32 c32 = col;
            Vector3 U(int st, int sl)
            {
                float phi = Mathf.PI * st / stacks, th = 2f * Mathf.PI * sl / slices;
                return new Vector3(Mathf.Sin(phi) * Mathf.Cos(th), Mathf.Cos(phi), Mathf.Sin(phi) * Mathf.Sin(th));
            }
            Vector3 Pt(int st, int sl) { var u = U(st, sl); return centre + q * Vector3.Scale(u, radii); }
            Vector3 Nm(int st, int sl) { var u = U(st, sl); return (q * new Vector3(u.x / radii.x, u.y / radii.y, u.z / radii.z)).normalized; }
            for (int st = 0; st < stacks; st++)
                for (int sl = 0; sl < slices; sl++)
                {
                    int i = _v.Count;
                    var a = Pt(st, sl); var b = Pt(st + 1, sl); var c = Pt(st + 1, sl + 1); var d = Pt(st, sl + 1);
                    _v.Add(a); _v.Add(b); _v.Add(c); _v.Add(d);
                    _n.Add(Nm(st, sl)); _n.Add(Nm(st + 1, sl)); _n.Add(Nm(st + 1, sl + 1)); _n.Add(Nm(st, sl + 1));
                    for (int k = 0; k < 4; k++) _c.Add(c32);
                    var nn = (_n[i] + _n[i + 2]) * 0.5f;
                    if (Vector3.Dot(Vector3.Cross(b - a, c - a), nn) >= 0f) _t.AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 });
                    else _t.AddRange(new[] { i, i + 2, i + 1, i, i + 3, i + 2 });
                }
            return this;
        }

        public Mesh Build(string name)
        {
            var m = new Mesh { name = name };
            m.SetVertices(_v); m.SetNormals(_n); m.SetColors(_c); m.SetTriangles(_t, 0);
            m.RecalculateBounds();
            return m;
        }
    }
}
