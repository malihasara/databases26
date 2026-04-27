// VioletConnect torch mark: white plate with violet flame, used in nav and as favicon.
export default function TorchLogo({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="VioletConnect torch"
    >
      <rect x="0" y="0" width="64" height="64" rx="8" fill="#5a189a" />
      <rect x="9" y="9" width="46" height="46" rx="2" fill="#ffffff" />
      <path
        d="M32 14
           c-1 5 -7 6 -7 12
           c0 4 3 7 7 7
           c4 0 7 -3 7 -7
           c0 -6 -6 -7 -7 -12 Z
           M28 16 c-2 4 -6 5 -6 11
           M36 16 c2 4 6 5 6 11"
        fill="#5a189a"
      />
      <rect x="22" y="33" width="20" height="3"  rx="1"   fill="#5a189a" />
      <rect x="29" y="36" width="6"  height="13"            fill="#5a189a" />
      <rect x="20" y="49" width="24" height="4"  rx="1"   fill="#5a189a" />
    </svg>
  );
}
