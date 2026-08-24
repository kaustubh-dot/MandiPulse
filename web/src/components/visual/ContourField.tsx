export function ContourField({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 520 320"
      data-visual="contour-field"
      aria-hidden="true"
      focusable="false"
      className={`pointer-events-none select-none text-rule ${className}`}
    >
      <path
        d="M42 198C66 92 190 36 310 62C430 88 490 150 470 230C450 310 336 300 244 274C152 248 18 304 42 198Z"
        fill="none"
        stroke="currentColor"
      />
      <path
        d="M86 196C104 120 200 76 300 94C400 112 446 158 430 218C414 278 326 266 250 246C174 226 68 272 86 196Z"
        fill="none"
        stroke="currentColor"
      />
      <path
        d="M132 194C146 144 214 112 290 124C366 136 402 166 390 208C378 250 314 238 254 224C194 210 118 244 132 194Z"
        fill="none"
        stroke="currentColor"
      />
      <path
        d="M178 192C188 164 230 146 282 154C334 162 360 178 350 202C340 226 302 216 258 208C214 200 168 220 178 192Z"
        fill="none"
        stroke="currentColor"
      />
      <path
        d="M76 250C170 226 214 178 286 160C356 142 408 116 470 74"
        fill="none"
        stroke="var(--mp-atlas)"
        strokeWidth="2"
      />
    </svg>
  );
}
