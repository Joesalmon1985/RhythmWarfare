using System;
using System.IO;

namespace Bedsit.Music
{
    /// <summary>Decoded audio held as interleaved stereo floats. Loaded from WAV (written by Tools/music/prepare_audio.py).</summary>
    public sealed class PcmClip
    {
        public float[] Data;          // interleaved L,R
        public int Frames;
        public int SampleRate;
        public string Name;
        public double Seconds => Frames / (double)SampleRate;

        public static PcmClip LoadWav(string path) { var c = FromBytes(File.ReadAllBytes(path)); c.Name = Path.GetFileName(path); return c; }

        public static PcmClip FromBytes(byte[] b)
        {
            if (b.Length < 44 || b[0] != 'R' || b[1] != 'I' || b[2] != 'F' || b[3] != 'F') throw new InvalidDataException("not a RIFF/WAV file");
            int pos = 12, channels = 2, sr = 48000, bits = 16, fmtTag = 1, dataPos = -1, dataLen = 0;
            while (pos + 8 <= b.Length)
            {
                string id = System.Text.Encoding.ASCII.GetString(b, pos, 4);
                int len = BitConverter.ToInt32(b, pos + 4);
                if (id == "fmt ")
                {
                    fmtTag = BitConverter.ToInt16(b, pos + 8);
                    channels = BitConverter.ToInt16(b, pos + 10);
                    sr = BitConverter.ToInt32(b, pos + 12);
                    bits = BitConverter.ToInt16(b, pos + 22);
                }
                else if (id == "data") { dataPos = pos + 8; dataLen = Math.Min(len, b.Length - dataPos); break; }
                pos += 8 + len + (len & 1);
            }
            if (dataPos < 0) throw new InvalidDataException("no data chunk");
            int bytesPer = bits / 8;
            int frames = dataLen / (bytesPer * channels);
            var d = new float[frames * 2];
            for (int i = 0; i < frames; i++)
            {
                for (int ch = 0; ch < 2; ch++)
                {
                    int src = Math.Min(ch, channels - 1);
                    int o = dataPos + (i * channels + src) * bytesPer;
                    float v;
                    if (fmtTag == 3 && bits == 32) v = BitConverter.ToSingle(b, o);
                    else if (bits == 16) v = BitConverter.ToInt16(b, o) / 32768f;
                    else if (bits == 24) v = ((b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)) << 8 >> 8) / 8388608f;
                    else throw new InvalidDataException("unsupported WAV format " + fmtTag + "/" + bits);
                    d[i * 2 + ch] = v;
                }
            }
            return new PcmClip { Data = d, Frames = frames, SampleRate = sr };
        }

        /// <summary>Linear-interpolation resample (only used when the audio device runs at a rate other than 48 kHz).</summary>
        public PcmClip Resampled(int newRate)
        {
            if (newRate == SampleRate) return this;
            double ratio = (double)SampleRate / newRate;
            int nf = (int)(Frames / ratio);
            var d = new float[nf * 2];
            for (int i = 0; i < nf; i++)
            {
                double s = i * ratio; int i0 = (int)s; double f = s - i0; int i1 = Math.Min(i0 + 1, Frames - 1);
                d[i * 2] = (float)(Data[i0 * 2] * (1 - f) + Data[i1 * 2] * f);
                d[i * 2 + 1] = (float)(Data[i0 * 2 + 1] * (1 - f) + Data[i1 * 2 + 1] * f);
            }
            return new PcmClip { Data = d, Frames = nf, SampleRate = newRate, Name = Name };
        }

        public static void SaveWav16(string path, float[] interleaved, int sampleRate, int channels = 2)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            using (var fs = new FileStream(path, FileMode.Create))
            using (var w = new BinaryWriter(fs))
            {
                int n = interleaved.Length;
                w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + n * 2); w.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));
                w.Write(16); w.Write((short)1); w.Write((short)channels); w.Write(sampleRate); w.Write(sampleRate * channels * 2); w.Write((short)(channels * 2)); w.Write((short)16);
                w.Write(System.Text.Encoding.ASCII.GetBytes("data")); w.Write(n * 2);
                for (int i = 0; i < n; i++) { float v = Math.Max(-1f, Math.Min(1f, interleaved[i])); w.Write((short)Math.Round(v * 32767f)); }
            }
        }
    }
}
