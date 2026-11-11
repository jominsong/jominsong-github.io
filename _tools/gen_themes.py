"""
12개 스킨을 각각 Sass로 컴파일해 최종 색상값을 뽑고,
[data-theme] 별 CSS 변수표(_themes.scss)와 _data/themes.yml 을 생성한다.

사용법 (저장소 루트에서):
    pip install libsass
    python3 _tools/gen_themes.py .

언제 쓰나: _sass/minimal-mistakes/skins/ 의 스킨 색을 바꾸거나 스킨을 추가/삭제했을 때.
결과물: _sass/minimal-mistakes/_themes.scss, _data/themes.yml (둘 다 덮어쓴다)
_ 로 시작하는 폴더라서 Jekyll 이 사이트에 포함하지 않는다.
"""
import os
import re
import sys

import sass

REPO = sys.argv[1]
SASS_DIR = os.path.join(REPO, "_sass")
SKIN_DIR = os.path.join(SASS_DIR, "minimal-mistakes", "skins")

# 스킨 이름 -> 설정 창에 보일 이름
LABELS = {
    "default": "Default",
    "air": "Air",
    "aqua": "Aqua",
    "contrast": "Contrast",
    "dark": "Dark",
    "dirt": "Dirt",
    "mint": "Mint",
    "neon": "Neon",
    "plum": "Plum",
    "sunrise": "Sunrise",
    "catppuccin_latte": "Catppuccin Latte",
    "catppuccin_mocha": "Catppuccin Mocha",
}
SKINS = list(LABELS)

# CSS 변수로 바꿀 SCSS 색상 변수 (파셜에서 실제로 쓰이는 것만)
THEMED = [
    "background-color", "text-color", "muted-text-color", "border-color",
    "code-background-color", "form-background-color", "footer-background-color",
    "primary-color", "success-color", "warning-color", "danger-color",
    "info-color", "focus-color", "active-color",
    "gray", "dark-gray", "light-gray",
    "link-color", "link-color-hover", "link-color-visited",
    "masthead-link-color", "masthead-link-color-hover", "navicon-link-color-hover",
    "notice-background-mix", "code-notice-background-mix",
    "base00", "base04", "base05", "base06", "base08", "base09",
    "base0a", "base0b", "base0c", "base0d", "base0e",
]
BTN = ["primary", "success", "warning", "danger", "info"]


def build_probe(skin):
    """스킨 하나를 적용한 뒤 모든 변수의 최종값을 :root 에 찍는 SCSS."""
    lines = []
    for name in THEMED:
        lines.append("  --%s: #{$%s};" % (name, name))
    # yiq 대비색: 빌드 때만 계산할 수 있어서 테마별로 미리 계산해 둔다
    for c in BTN:
        lines.append("  --%s-color-contrast: #{yiq-contrast-color($%s-color)};" % (c, c))
        lines.append(
            "  --%s-color-hover-contrast: #{yiq-contrast-color(mix(#000, $%s-color, 20%%))};" % (c, c)
        )
    lines.append("  --muted-text-color-contrast: #{yiq-contrast-color($muted-text-color)};")
    lines.append("  --active-color-contrast: #{yiq-contrast-color($active-color)};")
    body = "\n".join(lines)
    return f"""
// catppuccin_latte 스킨의 오타(mix2)를 mix 로 보정한다
@function mix2($a, $b, $w) {{ @return mix($a, $b, $w); }}
@import "minimal-mistakes/skins/{skin}";
@import "minimal-mistakes/variables";
@import "minimal-mistakes/mixins";
:root {{
{body}
}}
"""


def probe(skin):
    css = sass.compile(
        string=build_probe(skin),
        include_paths=[SASS_DIR],
        output_style="expanded",
    )
    m = re.search(r":root\s*\{([^}]*)\}", css)
    vals = {}
    for k, v in re.findall(r"--([\w-]+):\s*([^;]+);", m.group(1)):
        vals[k] = v.strip()
    return vals


def skin_extra_rules(skin):
    """스킨 파일에서 변수 선언을 빼고 남는 추가 CSS 규칙을 꺼낸다."""
    text = open(os.path.join(SKIN_DIR, f"_{skin}.scss"), encoding="utf-8").read()
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)          # /* */ 주석 제거
    text = re.sub(r"(?m)^\s*//.*$", "", text)            # // 주석 제거
    text = re.sub(r"(?m)^\s*\$[\w-]+\s*:[\s\S]*?;", "", text)  # 변수 선언 제거
    text = text.strip()
    if not text:
        return ""
    # 남은 규칙 안의 SCSS 변수를 CSS 변수로
    text = re.sub(r"\$([\w-]+)", r"var(--\1)", text)
    # // 주석(줄 끝)도 제거
    text = re.sub(r"\s//[^\n]*", "", text)
    return text


def luminance(hexcolor):
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000


def main():
    all_vals = {s: probe(s) for s in SKINS}
    base = all_vals["default"]

    out = []
    out.append("""/* ==========================================================================
   Themes (generated)
   설정 창에서 고르는 12개 테마의 색상표.
   각 스킨(skins/_*.scss)을 Sass 로 컴파일한 최종값이며, 스킨 파일이 바뀌면
   _tools/gen_themes.py 로 다시 만들어야 한다.
   - :root 는 default 테마 값 (data-theme 이 없을 때의 기본값)
   - [data-theme="..."] 는 default 와 다른 값만 덮어쓴다
   ========================================================================== */

""")

    meta = []
    for skin in SKINS:
        vals = all_vals[skin]
        bg = vals["background-color"]
        is_dark = luminance(bg) < 128
        meta.append((skin, LABELS[skin], "dark" if is_dark else "light"))
        selector = ":root" if skin == "default" else f':root[data-theme="{skin}"]'
        decls = []
        if skin == "default":
            decls.append("  color-scheme: light;")
            for k in vals:
                decls.append(f"  --{k}: {vals[k]};")
        else:
            decls.append(f"  color-scheme: {'dark' if is_dark else 'light'};")
            for k in vals:
                if vals[k] != base[k]:
                    decls.append(f"  --{k}: {vals[k]};")
        out.append(f"/* {LABELS[skin]} ({'dark' if is_dark else 'light'}) */\n")
        out.append(selector + " {\n" + "\n".join(decls) + "\n}\n\n")

    # 스킨별 추가 규칙: 원래는 스킨 import 위치(맨 앞)에서 나오던 규칙이다.
    # :where() 는 우선순위를 0으로 만들어서 원래 규칙과 같은 우선순위를 유지한다.
    out.append("/* 스킨별 추가 규칙 */\n")
    for skin in SKINS:
        extra = skin_extra_rules(skin)
        if not extra:
            continue
        out.append(f'/* {LABELS[skin]} */\n:where(:root[data-theme="{skin}"]) {{\n{extra}\n}}\n\n')

    path = os.path.join(SASS_DIR, "minimal-mistakes", "_themes.scss")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(out))

    yml = ["# 설정 창에 표시할 테마 목록 (_tools/gen_themes.py 로 생성)\n",
           "# mode: 배경 밝기로 나눈 라이트/다크 분류\n"]
    for name, label, mode in meta:
        yml.append(f"- name: {name}\n  label: \"{label}\"\n  mode: {mode}\n")
    ypath = os.path.join(REPO, "_data", "themes.yml")
    with open(ypath, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(yml))

    print("생성 완료:", path, ypath)
    for name, label, mode in meta:
        print(f"  {name:18s} {mode:5s} bg={all_vals[name]['background-color']}")


main()
