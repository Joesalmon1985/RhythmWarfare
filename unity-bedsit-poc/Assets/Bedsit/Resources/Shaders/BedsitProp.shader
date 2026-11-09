// Simple lit prop surface for the procedural clutter: albedo = material colour x per-vertex colour (so one mesh can have several colours),
// with an optional emissive "flash" used for hover / tidy feedback. Lives in Resources so it is always included in player builds.
Shader "Bedsit/Prop"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _Flash ("Flash", Range(0,1)) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        CGPROGRAM
        #pragma surface surf Lambert addshadow
        fixed4 _Color;
        half _Flash;
        struct Input { float4 color : COLOR; };
        void surf (Input IN, inout SurfaceOutput o)
        {
            o.Albedo = _Color.rgb * IN.color.rgb;
            o.Emission = _Flash * fixed3(1.0, 0.92, 0.65);
            o.Alpha = 1;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
