// Flat, self-lit tint used by the interaction cue (a gently rotating marker above whatever the top control would act on).
Shader "Bedsit/Cue"
{
    Properties
    {
        _Color ("Color", Color) = (0.35, 1.0, 0.45, 1)
        _Pulse ("Pulse", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry+10" }
        Lighting Off
        ZTest LEqual
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            fixed4 _Color;
            float _Pulse;
            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; };
            struct v2f { float4 pos : SV_POSITION; float3 n : TEXCOORD0; };
            v2f vert (appdata v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.n = UnityObjectToWorldNormal(v.normal); return o; }
            fixed4 frag (v2f i) : SV_Target
            {
                float shade = 0.65 + 0.35 * saturate(dot(normalize(i.n), normalize(float3(0.3, 0.8, -0.5))));
                return fixed4(_Color.rgb * shade * _Pulse, 1);
            }
            ENDCG
        }
    }
}
