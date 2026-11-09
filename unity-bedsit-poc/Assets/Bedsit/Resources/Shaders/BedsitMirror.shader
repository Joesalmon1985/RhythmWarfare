// Samples the mirror camera's RenderTexture on the mirror surface (UV-mapped, so no screen-space tricks are needed:
// the reflection camera is built with an off-axis frustum through the mirror's frame).
Shader "Bedsit/Mirror"
{
    Properties
    {
        _MainTex ("Reflection", 2D) = "black" {}
        _Tint ("Tint", Color) = (0.93, 0.97, 1.0, 1)
        _Edge ("Edge falloff", Range(0, 0.2)) = 0.02
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        Cull Off
        Lighting Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            fixed4 _Tint;
            float _Edge;

            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 c = tex2D(_MainTex, i.uv) * _Tint;
                float2 d = min(i.uv, 1.0 - i.uv);
                float e = saturate(min(d.x, d.y) / max(_Edge, 0.0001));
                c.rgb *= lerp(0.55, 1.0, e);          // faint darkening towards the glass edge
                c.a = 1;
                return c;
            }
            ENDCG
        }
    }
}
