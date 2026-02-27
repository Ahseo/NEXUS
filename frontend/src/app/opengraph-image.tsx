import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "WINGMAN – Autonomous Networking Agent";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#F7F7F4",
        }}
      >
        <svg
          width="120"
          height="128"
          viewBox="0 0 134 143"
          fill="none"
        >
          <path
            d="M56.9257 84.4363L22.6063 31.5891L7.61395 57.9942L41.9341 110.843"
            fill="black"
          />
          <path
            d="M126.381 84.8954L92.0614 32.0481L77.0691 58.4532L111.389 111.302"
            fill="black"
          />
          <path
            d="M88.4812 79.6986L61.3594 37.9346L46.3671 64.3398L73.4897 106.105"
            fill="black"
          />
        </svg>
        <div
          style={{
            marginTop: 32,
            fontSize: 64,
            fontWeight: 700,
            letterSpacing: "-0.03em",
            color: "#1a1a1a",
          }}
        >
          WINGMAN
        </div>
        <div
          style={{
            marginTop: 12,
            fontSize: 24,
            color: "#8a8a8a",
          }}
        >
          Your autonomous networking agent
        </div>
      </div>
    ),
    { ...size }
  );
}
