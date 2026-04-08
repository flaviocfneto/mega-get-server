import React from "react";

type Variant = "color" | "mono" | "favicon";

interface FtIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  variant?: Variant;
  title?: string | null;
}

/**
 * FileTugger brand glyph — rounded paper document with a top-left folded
 * corner (cranberry underside), overlaid by two interlocking gold/teal chain
 * links on a -43° diagonal. The fold sits in the upper-left of the tile,
 * clear of the chain's upper-right endpoint. Palette: Fjord.
 *
 *   document body   #F4F5F3  (paper)
 *   document fold   #BE123C  (cranberry accent)
 *   document line   #0F1713  (near-black)
 *   gold chain      #F5B82E
 *   teal chain      #2DD4BF
 */
export const FtIcon: React.FC<FtIconProps> = ({
  size = 48,
  variant = "color",
  title = "FileTugger",
  ...rest
}) => {
  const decorative = title === null;
  const a11y = decorative
    ? { "aria-hidden": true as const, focusable: false as const }
    : { role: "img" as const, "aria-label": title as string };

  const docPath =
    "M 182 66 L 358 66 Q 406 66 406 114 L 406 398 Q 406 446 358 446 L 154 446 Q 106 446 106 398 L 106 142 Z";
  const foldFill = "M 182 66 L 106 142 L 182 142 Z";
  const foldCrease = "M 182 66 L 182 142 L 106 142";

  if (variant === "favicon") {
    const docSm = "M 23 8 L 45 8 Q 51 8 51 14 L 51 50 Q 51 56 45 56 L 19 56 Q 13 56 13 50 L 13 18 Z";
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width={size} height={size} {...a11y} {...rest}>
        <g transform="rotate(-13 32 32)">
          <path d={docSm} fill="#F4F5F3" />
          <path d="M 23 8 L 13 18 L 23 18 Z" fill="#BE123C" />
          <path d={docSm} fill="none" stroke="#0F1713" strokeWidth="3" strokeLinejoin="round" />
          <path d="M 23 8 L 23 18 L 13 18" fill="none" stroke="#0F1713" strokeWidth="3" strokeLinejoin="round" />
        </g>
        <g transform="rotate(-43 32 32)">
          <rect x="-3" y="22" width="52" height="20" rx="10" fill="none" stroke="#F5B82E" strokeWidth="5.5" />
          <rect x="15" y="22" width="52" height="20" rx="10" fill="none" stroke="#2DD4BF" strokeWidth="5.5" />
          <path d="M -3 32 A 10 10 0 0 0 7 42 L 39 42 A 10 10 0 0 0 49 32" fill="none" stroke="#F5B82E" strokeWidth="5.5" />
        </g>
      </svg>
    );
  }

  if (variant === "mono") {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width={size} height={size} {...a11y} {...rest}>
        <defs>
          <mask id="ft-gold-cut" maskUnits="userSpaceOnUse" x="-200" y="-200" width="900" height="900">
            <rect x="-200" y="-200" width="900" height="900" fill="white" />
            <circle cx="310" cy="176" r="32" fill="black" />
            <circle cx="202" cy="176" r="32" fill="black" />
          </mask>
          <mask id="ft-teal-cut" maskUnits="userSpaceOnUse" x="-200" y="-200" width="900" height="900">
            <rect x="-200" y="-200" width="900" height="900" fill="white" />
            <circle cx="310" cy="336" r="32" fill="black" />
            <circle cx="202" cy="336" r="32" fill="black" />
          </mask>
        </defs>
        <g transform="rotate(-13 256 256)" fill="none" stroke="currentColor" strokeWidth="14" strokeLinejoin="round" opacity="0.5">
          <path d={docPath} />
          <path d={foldCrease} />
        </g>
        <g transform="rotate(-43 256 256)" fill="none" stroke="currentColor" strokeWidth="38">
          <rect x="-30" y="176" width="420" height="160" rx="80" mask="url(#ft-gold-cut)" />
          <rect x="122" y="176" width="420" height="160" rx="80" mask="url(#ft-teal-cut)" />
        </g>
      </svg>
    );
  }

  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width={size} height={size} {...a11y} {...rest}>
      <g transform="rotate(-13 256 256)">
        <path d={docPath} fill="#F4F5F3" />
        <path d={foldFill} fill="#BE123C" />
        <path d={docPath} fill="none" stroke="#0F1713" strokeWidth="7" strokeLinejoin="round" />
        <path d={foldCrease} fill="none" stroke="#0F1713" strokeWidth="7" strokeLinejoin="round" />
      </g>
      <g transform="rotate(-43 256 256)">
        <rect x="-30" y="176" width="420" height="160" rx="80" fill="none" stroke="#F5B82E" strokeWidth="38" />
        <rect x="122" y="176" width="420" height="160" rx="80" fill="none" stroke="#2DD4BF" strokeWidth="38" />
        <path d="M -30 256 A 80 80 0 0 0 50 336 L 310 336 A 80 80 0 0 0 390 256" fill="none" stroke="#F5B82E" strokeWidth="38" />
      </g>
    </svg>
  );
};

export default FtIcon;
