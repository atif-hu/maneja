export function BotanicalArt({ variant = "login" }: { variant?: "login" | "signup" }) {
  if (variant === "signup") {
    return (
      <svg viewBox="0 0 520 956" className="botanical-art" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="M80 1010C88 855 175 782 157 637C139 493 32 429 87 285C132 168 261 133 232 -33" stroke="#E7B6AE" strokeWidth="1.5" />
        <path d="M164 1007C170 851 252 797 238 649C225 509 125 449 177 315C218 209 335 164 309 6" stroke="#DFA9A3" strokeWidth="1.2" />
        <path d="M278 1005C265 881 350 790 334 668C315 521 240 474 292 363C335 272 441 248 419 105" stroke="#E7B6AE" strokeWidth="1.5" />
        <path d="M372 1000C354 876 438 803 421 698C402 577 344 529 391 432C429 354 507 332 487 220" stroke="#DFA9A3" strokeWidth="1.2" />
        <path d="M151 566C102 521 102 465 137 424C176 379 231 397 247 448C260 492 215 544 151 566Z" stroke="#E2ACA6" strokeWidth="1.2" />
        <path d="M334 744C282 697 286 638 324 607C366 572 414 604 424 653C434 701 395 735 334 744Z" stroke="#E2ACA6" strokeWidth="1.2" />
        <path d="M234 250C195 220 200 175 232 150C266 123 307 145 316 183C325 219 291 244 234 250Z" stroke="#E2ACA6" strokeWidth="1.2" />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 520 956"
      className="botanical-art"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Abstract flowing botanical line illustration"
    >
      <path
        d="M438 100C346 164 344 248 393 300C447 357 451 426 366 469C281 512 242 570 278 644C314 718 398 700 433 765C459 814 425 865 342 921"
        stroke="#F59197"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.78"
      />
      <path
        d="M447 152C401 189 387 238 414 274C441 310 438 354 386 377C325 404 282 445 296 494C310 543 365 551 375 603C386 655 350 693 303 723"
        stroke="#D9A79D"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.8"
      />
      <path d="M389 299C342 282 302 295 279 328C319 342 354 332 389 299Z" stroke="#F59197" strokeWidth="1.5" />
      <path d="M374 469C322 446 278 458 254 494C300 508 340 499 374 469Z" stroke="#D9A79D" strokeWidth="1.5" />
      <path d="M279 644C230 625 188 643 171 681C215 690 253 678 279 644Z" stroke="#F59197" strokeWidth="1.5" />
      <path d="M433 765C391 739 351 744 329 777C367 793 403 789 433 765Z" stroke="#D9A79D" strokeWidth="1.5" />
      <path d="M438 100C407 75 375 78 355 105C387 119 415 116 438 100Z" stroke="#D9A79D" strokeWidth="1.5" />
      <circle cx="438" cy="100" r="5" fill="#F59197" />
      <circle cx="278" cy="644" r="4" fill="#D9A79D" />
    </svg>
  );
}
