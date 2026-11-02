"""Author the three theme-aware warehouse scenes used by the executive brief."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "executive"


def label(x, y, en, es, size=22):
    return "".join(
        f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" '
        f'fill="var(--color-fg)" data-lang="{lang}">{text}</text>'
        for lang, text in (("en", en), ("es", es))
    )


def person(x, y, color="--color-accent"):
    return (f'<g transform="translate({x} {y})"><circle cy="-34" r="13" fill="var({color})"/>'
            f'<path d="M-21 9V-9Q-21-22 0-22T21-9V9M-10 9V39M10 9V39" '
            f'fill="none" stroke="var({color})" stroke-width="12" stroke-linecap="round"/></g>')


def crate(x, y, color="--color-warn", extra=""):
    return (f'<g transform="translate({x} {y})" {extra}>'
            f'<rect width="36" height="29" rx="3" fill="var({color})" opacity=".78"/>'
            '<path d="M18 1V11M10 15H25" stroke="var(--color-bg)" stroke-width="3"/></g>')


def wrap(title, drawing, animated=False):
    motion = """
    <style>
      .arrival { animation: arrive 8s ease-in-out infinite; }
      .arrival-two { animation-delay: 1s; }
      @keyframes arrive { 0%,15% { opacity: 0; transform: translateY(-10px); } 40%,100% { opacity: 1; transform: translateY(0); } }
      @media (prefers-reduced-motion: reduce) { .arrival { animation: none; } }
    </style>""" if animated else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" role="img">'
            f'<title>{title}</title>{motion}'
            '<rect x="8" y="8" width="784" height="384" rx="28" fill="var(--color-surface)"/>'
            '<path d="M30 329H770" stroke="var(--color-border)" stroke-width="3"/>'
            f'{drawing}</svg>\n')


def warehouse(proposed=False):
    drawing = (
        '<path d="M35 142L220 72L405 142V320H35Z" fill="var(--color-surface-2)" '
        'stroke="var(--color-border)" stroke-width="3"/>'
        '<path d="M55 165H385M55 218H385M55 271H385M65 165V318M375 165V318" '
        'stroke="var(--color-fg-faint)" stroke-width="5"/>'
        '<path d="M447 320V246H613V320" fill="none" stroke="var(--color-fg-subtle)" stroke-width="9"/>'
        '<rect x="472" y="167" width="116" height="70" rx="8" fill="var(--color-bg)" '
        'stroke="var(--color-accent)" stroke-width="4"/>'
        '<path d="M514 239H546" stroke="var(--color-fg-subtle)" stroke-width="5"/>'
        '<path d="M633 264H708L738 288V319H633Z" fill="var(--color-accent)" opacity=".8"/>'
        '<path d="M709 273V291H730" fill="none" stroke="var(--color-bg)" stroke-width="4"/>'
        '<circle cx="657" cy="320" r="14" fill="var(--color-fg-subtle)"/>'
        '<circle cx="717" cy="320" r="14" fill="var(--color-fg-subtle)"/>'
        '<circle cx="687" cy="84" r="29" fill="var(--color-bg)" '
        'stroke="var(--color-fg-faint)" stroke-width="3"/>'
        '<path d="M687 64V84L700 93" fill="none" stroke="var(--color-fg-subtle)" stroke-width="4"/>'
    )
    drawing += label(220, 135, "Inventory", "Inventario")
    drawing += label(530, 135, "Planning", "Planificación")
    drawing += label(690, 363, "Commitments", "Compromisos", 20)
    drawing += label(220, 363, "Matched flow" if proposed else "Uneven stock",
                     "Flujo ajustado" if proposed else "Existencias desiguales", 20)
    drawing += person(433, 208)
    if proposed:
        for x in (85, 140, 195, 250, 305):
            drawing += crate(x, 181, "--color-good")
        for x in (85, 195, 305):
            drawing += crate(x, 234, "--color-good")
        drawing += '<path d="M490 197L502 209L524 185M540 191H570M540 206H563" fill="none" stroke="var(--color-good)" stroke-width="5"/>'
        drawing += person(753, 218, "--color-good")
    else:
        for x in (85, 124, 163, 202, 241, 280, 319):
            drawing += crate(x, 181)
        drawing += crate(310, 234, "--color-warn", 'class="arrival"')
        drawing += crate(310, 277, "--color-warn", 'class="arrival arrival-two"')
        drawing += '<path d="M490 183L517 212M517 183L490 212M540 185H569M540 201H561M540 217H572" fill="none" stroke="var(--color-warn)" stroke-width="4"/>'
        drawing += person(669, 202, "--color-warn") + person(723, 202, "--color-warn")
    return wrap("Planning and demand in a warehouse", drawing, animated=not proposed)


def situation():
    drawing = '<path d="M45 128L400 55L755 128V320H45Z" fill="var(--color-surface-2)" stroke="var(--color-border)" stroke-width="3"/>'
    for x, en, es in ((150, "Plan", "Planificar"), (400, "Operate", "Operar"), (650, "Review", "Revisar")):
        drawing += person(x - 39, 205)
        drawing += (f'<path d="M{x-78} 318V257H{x+75}V318" fill="none" '
                    'stroke="var(--color-fg-subtle)" stroke-width="8"/>')
        drawing += label(x, 365, en, es)
    drawing += '<rect x="149" y="193" width="65" height="52" rx="5" fill="var(--color-bg)" stroke="var(--color-accent)" stroke-width="3"/>'
    drawing += '<path d="M163 207H200M163 219H192M163 231H204" stroke="var(--color-fg-faint)" stroke-width="3"/>'
    drawing += crate(409, 224) + crate(449, 224)
    drawing += '<rect x="648" y="180" width="65" height="63" rx="5" fill="var(--color-bg)" stroke="var(--color-accent)" stroke-width="3"/>'
    drawing += '<path d="M658 196L666 204L680 188M658 222H700M684 198H701" fill="none" stroke="var(--color-good)" stroke-width="4"/>'
    drawing += label(400, 112, "One shared decision", "Una decisión compartida")
    return wrap("Three roles in the planning process", drawing)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in (("pain", warehouse()), ("situation", situation()), ("proposal", warehouse(True))):
        (OUT / f"{name}.svg").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
