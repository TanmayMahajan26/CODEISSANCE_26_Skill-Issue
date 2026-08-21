"use client";

import dynamic from "next/dynamic";

const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d"),
  { ssr: false }
);

export default ForceGraph2D;
