import asyncio
import flet as ft
import json, os, re, shlex, subprocess, sys
from datetime import datetime

# ── Material Design 3 · Teal · Light ─────────────────────────
PRIMARY              = "#006A60"
ON_PRIMARY           = "#FFFFFF"
PRIMARY_CONTAINER    = "#9EF2E4"
ON_PRIMARY_CONTAINER = "#00201C"
SURFACE              = "#FAFDFB"
SURFACE_VARIANT      = "#DAE5E2"
ON_SURFACE           = "#191C1B"
ON_SURFACE_VARIANT   = "#3F4947"
OUTLINE_VARIANT      = "#BFC9C5"
ERROR                = "#BA1A1A"

DATA_FILE = os.path.join(os.path.expanduser("~"), ".claude_sessions.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def parse_text(text: str):
    cmd = re.search(r"(claude\s+--resume\s+[a-f0-9-]+)", text)
    # Windows PowerShell:  PS C:\path>
    d = re.search(r"PS\s+([A-Za-z]:[^>]+)>", text)
    # macOS / Linux shell: /path/to/dir$ 或 ~/path$
    if not d:
        d = re.search(r"(?:^|\n)((?:/|~)[^\n$#]*?)(?:\s*[\(\[].*?[\)\]])?\s*[$#]",
                      text, re.MULTILINE)
    if cmd and d:
        return {
            "time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "directory": d.group(1).strip(),
            "command":   cmd.group(1).strip(),
        }
    return None


# ── 跨平台原生对话框 / 剪贴板 ────────────────────────────────
def _run(args: list, timeout: int = 120) -> str:
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else ""


def _try_cmds(cmds: list, timeout: int = 120) -> str:
    for args in cmds:
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0:
                return r.stdout.strip()
        except FileNotFoundError:
            continue
    return ""


def _ps_save_dialog() -> str:
    if sys.platform == "win32":
        return _run(["powershell", "-NonInteractive", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.SaveFileDialog;"
            "$d.Title = '导出数据库';"
            "$d.Filter = 'JSON 文件|*.json';"
            "$d.FileName = 'claude_sessions_backup.json';"
            "$d.DefaultExt = 'json';"
            "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.FileName }"])
    elif sys.platform == "darwin":
        return _run(["osascript", "-e",
            'POSIX path of (choose file name with prompt "导出数据库" '
            'default name "claude_sessions_backup.json")'])
    else:
        return _try_cmds([
            ["zenity", "--file-selection", "--save", "--confirm-overwrite",
             "--title=导出数据库", "--filename=claude_sessions_backup.json",
             "--file-filter=JSON files | *.json"],
            ["kdialog", "--getsavefilename", "claude_sessions_backup.json", "*.json"],
        ])


def _ps_open_dialog() -> str:
    if sys.platform == "win32":
        return _run(["powershell", "-NonInteractive", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.OpenFileDialog;"
            "$d.Title = '导入数据库';"
            "$d.Filter = 'JSON 文件|*.json';"
            "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.FileName }"])
    elif sys.platform == "darwin":
        return _run(["osascript", "-e",
            'POSIX path of (choose file with prompt "导入数据库" '
            'of type {"json", "public.json"})'])
    else:
        return _try_cmds([
            ["zenity", "--file-selection", "--title=导入数据库",
             "--file-filter=JSON files | *.json"],
            ["kdialog", "--getopenfilename", ".", "*.json"],
        ])


def _ps_clipboard() -> str:
    if sys.platform == "win32":
        return _run(["powershell", "-NonInteractive", "-Command", "Get-Clipboard"],
                    timeout=10)
    elif sys.platform == "darwin":
        return _run(["pbpaste"], timeout=10)
    else:
        return _try_cmds([
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel",  "--clipboard", "--output"],
            ["wl-paste"],
        ], timeout=10)


async def run_in_thread(fn):
    return await asyncio.get_event_loop().run_in_executor(None, fn)


# ─────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title             = "Claude 历史记录管理"
    page.theme_mode        = ft.ThemeMode.LIGHT
    page.bgcolor           = SURFACE
    page.padding           = 0
    page.window.width      = 1040
    page.window.height     = 700
    page.window.min_width  = 860
    page.window.min_height = 560
    page.theme = ft.Theme(
        font_family="Noto Sans SC",
        color_scheme_seed="#00897B",
        use_material3=True,
    )

    records      = load_data()
    selected_rec = [None]

    # ── SnackBar ──────────────────────────────────────────────
    _snack = ft.SnackBar(ft.Text(""), bgcolor=PRIMARY)
    page.overlay.append(_snack)

    def snack(msg: str, color: str = PRIMARY):
        _snack.content = ft.Text(msg, color=ON_PRIMARY, weight=ft.FontWeight.W_500)
        _snack.bgcolor  = color
        _snack.open     = True
        page.update()

    # ── Paste area ────────────────────────────────────────────
    paste_tf = ft.TextField(
        multiline=True, min_lines=3, max_lines=5,
        hint_text="粘贴 Claude 会话信息：Resume this session with: claude --resume ... / PS C:\\...>",
        border_color=OUTLINE_VARIANT,
        focused_border_color=PRIMARY,
        hint_style=ft.TextStyle(color=ON_SURFACE_VARIANT, size=12),
        text_style=ft.TextStyle(font_family="JetBrains Mono", size=12),
        border_radius=8,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )

    async def do_paste_clipboard(e):
        text = await run_in_thread(_ps_clipboard)
        if not text:
            snack("剪贴板为空", ERROR); return
        paste_tf.value = text
        page.update()
        _do_save()

    def _do_save():
        rec = parse_text(paste_tf.value or "")
        if rec:
            records.append(rec)
            save_data(records)
            paste_tf.value = ""
            refresh_table()
            snack(f"已保存  {rec['time']}")
        else:
            snack("格式无法识别，请检查内容", ERROR)
        page.update()

    def do_save(e): _do_save()
    def do_clear(e):
        paste_tf.value = ""; page.update()

    # ── Search ────────────────────────────────────────────────
    search_tf = ft.TextField(
        hint_text="搜索目录、命令或时间…",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        border_color=OUTLINE_VARIANT,
        focused_border_color=PRIMARY,
        border_radius=24,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        text_style=ft.TextStyle(size=13),
        expand=True,
        on_change=lambda e: refresh_table(e.control.value or ""),
    )
    count_lbl = ft.Text("", size=12, color=ON_SURFACE_VARIANT)

    # ── Column widths（可拖拽调节）──────────────────────────────
    col_w = [158, 360]   # [时间宽度, 目录宽度]，Resume命令列 expand 填满
    MIN_COL = 80

    # 表头标签引用，拖拽时直接更新 width 属性
    hdr_time_lbl = ft.Text("时间", size=12, width=col_w[0],
                            weight=ft.FontWeight.W_600, color=ON_SURFACE)
    hdr_dir_lbl  = ft.Text("目录", size=13, width=col_w[1],
                            weight=ft.FontWeight.W_600, color=ON_SURFACE)

    def _drag_divider(idx: int, h: int = 20) -> ft.GestureDetector:
        """拖拽分割线：拖动调整相邻列宽"""
        def on_drag(e):
            dx = e.primary_delta or 0.0
            if idx == 0:
                n0, n1 = col_w[0] + dx, col_w[1] - dx
                if n0 >= MIN_COL and n1 >= MIN_COL:
                    col_w[0], col_w[1] = n0, n1
            else:
                n1 = col_w[1] + dx
                if n1 >= MIN_COL:
                    col_w[1] = n1
            hdr_time_lbl.width = col_w[0]
            hdr_dir_lbl.width  = col_w[1]
            refresh_table(search_tf.value or "")

        return ft.GestureDetector(
            content=ft.Container(
                width=5, height=h,
                bgcolor=OUTLINE_VARIANT,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN,
            on_horizontal_drag_update=on_drag,
        )

    def _row_container(r) -> ft.Container:
        is_sel = (
            selected_rec[0] is not None
            and selected_rec[0]["time"]    == r["time"]
            and selected_rec[0]["command"] == r["command"]
        )

        def on_click(e, rec=r):
            selected_rec[0] = None if (
                selected_rec[0] is not None
                and selected_rec[0]["time"]    == rec["time"]
                and selected_rec[0]["command"] == rec["command"]
            ) else rec
            refresh_table(search_tf.value or "")

        return ft.Container(
            ft.Row(
                [
                    ft.Text(
                        r["time"], size=11, width=col_w[0],
                        font_family="JetBrains Mono",
                        color=ON_SURFACE_VARIANT,
                        no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(width=1, height=20, bgcolor=OUTLINE_VARIANT),
                    ft.Text(
                        r["directory"], size=13, width=col_w[1],
                        color=ON_SURFACE,
                        no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(width=1, height=20, bgcolor=OUTLINE_VARIANT),
                    ft.Text(
                        r["command"], size=11, expand=True,
                        font_family="JetBrains Mono",
                        color=ON_SURFACE,
                        no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=PRIMARY_CONTAINER if is_sel else SURFACE,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, OUTLINE_VARIANT)),
            on_click=on_click,
            ink=True,
        )

    table_header = ft.Container(
        ft.Row(
            [
                hdr_time_lbl,
                _drag_divider(0, h=16),
                hdr_dir_lbl,
                _drag_divider(1, h=16),
                ft.Text("Resume 命令", size=13, expand=True,
                        weight=ft.FontWeight.W_600, color=ON_SURFACE),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_VARIANT,
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        border=ft.Border(bottom=ft.BorderSide(1, OUTLINE_VARIANT)),
    )

    table_list = ft.ListView(expand=True, spacing=0)

    def refresh_table(filter_text: str = ""):
        fl = filter_text.lower()
        filtered = [
            r for r in reversed(records)
            if not fl
               or fl in r["time"].lower()
               or fl in r["directory"].lower()
               or fl in r["command"].lower()
        ]
        table_list.controls = [_row_container(r) for r in filtered]
        total = len(records); shown = len(filtered)
        count_lbl.value = (
            f"共 {total} 条" if not filter_text
            else f"显示 {shown} / {total} 条"
        )
        page.update()

    # ── Execute ───────────────────────────────────────────────
    def do_execute(e):
        rec = selected_rec[0]
        if not rec: snack("请先点击选择一条记录", ERROR); return
        d, cmd = rec["directory"], rec["command"]

        if sys.platform == "win32":
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command",
                 f'Set-Location -Path "{d}"; {cmd}'],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        elif sys.platform == "darwin":
            shell = f"cd {shlex.quote(d)} && {cmd}"
            escaped = shell.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.Popen([
                "osascript",
                "-e", f'tell application "Terminal" to do script "{escaped}"',
                "-e",  'tell application "Terminal" to activate',
            ])
        else:
            shell = f"cd {shlex.quote(d)} && {cmd}; exec bash"
            launched = False
            for term in [
                ["gnome-terminal", "--", "bash", "-c", shell],
                ["xfce4-terminal", "-e", f"bash -c {shlex.quote(shell)}"],
                ["konsole", "--noclose", "-e", "bash", "-c", shell],
                ["xterm", "-e", f"bash -c {shlex.quote(shell)}"],
            ]:
                try:
                    subprocess.Popen(term); launched = True; break
                except FileNotFoundError:
                    continue
            if not launched:
                snack("未找到可用终端模拟器", ERROR)

    # ── Delete ────────────────────────────────────────────────
    def do_delete(e):
        rec = selected_rec[0]
        if not rec: snack("请先点击选择一条记录", ERROR); return

        def confirm(ev):
            records[:] = [
                r for r in records
                if not (r["time"] == rec["time"] and r["command"] == rec["command"])
            ]
            save_data(records)
            selected_rec[0] = None
            refresh_table(search_tf.value or "")
            page.pop_dialog(); snack("已删除")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.W_500),
            content=ft.Container(
                ft.Column([
                    ft.Text(rec["time"],      size=11, font_family="JetBrains Mono", color=ON_SURFACE_VARIANT),
                    ft.Text(rec["directory"], size=13, color=ON_SURFACE),
                    ft.Text(rec["command"],   size=11, font_family="JetBrains Mono", color=ON_SURFACE),
                ], spacing=4, tight=True),
                padding=ft.Padding.only(top=8),
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: page.pop_dialog()),
                ft.FilledButton("删除", on_click=confirm,
                    style=ft.ButtonStyle(bgcolor=ERROR, color=ON_PRIMARY)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    # ── Export ────────────────────────────────────────────────
    async def do_export(e):
        path = await run_in_thread(_ps_save_dialog)
        if not path: return
        if not path.endswith(".json"): path += ".json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        snack(f"已导出 {len(records)} 条记录")

    # ── Import ────────────────────────────────────────────────
    async def do_import(e):
        path = await run_in_thread(_ps_open_dialog)
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                incoming = json.load(f)
            if not isinstance(incoming, list): raise ValueError("顶层不是数组")
            for item in incoming:
                if not all(k in item for k in ("time", "directory", "command")):
                    raise ValueError("记录缺少必要字段")
        except Exception as ex:
            snack(f"解析错误：{ex}", ERROR); return

        def do_merge(ev):
            keys = {(r["time"], r["command"]) for r in records}
            added = 0
            for r in incoming:
                k = (r["time"], r["command"])
                if k not in keys:
                    records.append(r); keys.add(k); added += 1
            save_data(records); selected_rec[0] = None
            refresh_table(search_tf.value or "")
            page.pop_dialog()
            snack(f"合并完成：新增 {added} 条，跳过重复 {len(incoming)-added} 条")

        def do_replace(ev):
            records.clear(); records.extend(incoming)
            save_data(records); selected_rec[0] = None
            refresh_table(search_tf.value or "")
            page.pop_dialog(); snack(f"已替换为 {len(records)} 条记录")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("选择导入方式", size=18, weight=ft.FontWeight.W_500),
            content=ft.Container(
                ft.Column([
                    ft.Text(f"即将导入 {len(incoming)} 条记录", size=14, color=ON_SURFACE),
                    ft.Text("合并：追加新记录，自动去重",         size=13, color=ON_SURFACE_VARIANT),
                    ft.Text("替换：清空现有记录并替换为导入内容",  size=13, color=ERROR),
                ], spacing=6, tight=True),
                padding=ft.Padding.only(top=8),
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: page.pop_dialog()),
                ft.FilledTonalButton("合并", on_click=do_merge),
                ft.FilledButton("替换", on_click=do_replace,
                    style=ft.ButtonStyle(bgcolor=ERROR, color=ON_PRIMARY)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    # ── Init ──────────────────────────────────────────────────
    refresh_table()

    # ── Layout ────────────────────────────────────────────────
    page.add(
        ft.Column(
            [
                # ── AppBar ────────────────────────────────────
                ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.MANAGE_HISTORY_ROUNDED, color=ON_PRIMARY, size=24),
                        ft.Text("Claude 历史记录管理",
                                size=20, weight=ft.FontWeight.W_500, color=ON_PRIMARY),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=PRIMARY,
                    padding=ft.Padding.symmetric(horizontal=24),
                    height=64,
                ),

                # ── Body ──────────────────────────────────────
                ft.Container(
                    ft.Column(
                        [
                            # 粘贴区域
                            ft.Container(
                                ft.Column(
                                    [
                                        paste_tf,
                                        ft.Row(
                                            [
                                                ft.FilledButton(
                                                    "从剪贴板粘贴",
                                                    icon=ft.Icons.CONTENT_PASTE_ROUNDED,
                                                    on_click=do_paste_clipboard,
                                                ),
                                                ft.FilledTonalButton(
                                                    "保存内容",
                                                    icon=ft.Icons.SAVE_ROUNDED,
                                                    on_click=do_save,
                                                ),
                                                ft.TextButton("清空", on_click=do_clear),
                                            ],
                                            spacing=8,
                                        ),
                                    ],
                                    spacing=8,
                                    tight=True,
                                ),
                                padding=ft.Padding.all(16),
                                border=ft.Border.all(1, OUTLINE_VARIANT),
                                border_radius=8,
                                bgcolor=SURFACE,
                            ),

                            # 搜索行
                            ft.Row(
                                [search_tf, count_lbl],
                                spacing=16,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),

                            # 表格（header + 列表）
                            ft.Container(
                                ft.Column(
                                    [table_header, table_list],
                                    spacing=0,
                                    expand=True,
                                ),
                                expand=True,
                                border=ft.Border.all(1, OUTLINE_VARIANT),
                                border_radius=12,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                bgcolor=SURFACE,
                            ),

                            # 操作栏
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "执行选中",
                                        icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                        on_click=do_execute,
                                    ),
                                    ft.OutlinedButton(
                                        "删除选中",
                                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                        on_click=do_delete,
                                        style=ft.ButtonStyle(color=ERROR),
                                    ),
                                    ft.Container(
                                        width=1, bgcolor=OUTLINE_VARIANT, height=32,
                                        margin=ft.Margin.symmetric(horizontal=8),
                                    ),
                                    ft.FilledTonalButton(
                                        "导出", icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                        on_click=do_export,
                                    ),
                                    ft.FilledTonalButton(
                                        "导入", icon=ft.Icons.DOWNLOAD_ROUNDED,
                                        on_click=do_import,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=12,
                        expand=True,
                    ),
                    padding=ft.Padding.all(20),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )


ft.run(main)
