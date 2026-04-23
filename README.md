# Claude 历史记录管理

一个用于归档和快速恢复 Claude CLI 会话的 Windows 桌面工具。

---

## 功能特性

- **一键归档**：将 Claude CLI 输出的 `claude --resume <id>` 与 `PS C:\...>` 信息粘贴进来，自动提取时间、目录、Resume 命令并保存
- **即时搜索**：按时间、目录或命令关键词实时过滤记录
- **一键恢复**：选中记录后点击"执行选中"，自动打开新 PowerShell 窗口并 `cd` 到对应目录、执行 Resume 命令
- **可调列宽**：拖拽表头的列分隔线，自由调整各列显示宽度
- **导入 / 导出**：将数据库备份为 JSON 文件，或从备份文件合并/替换导入
- **数据持久化**：记录保存在 `~/.claude_sessions.json`，跨会话保留

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| 运行时 | 无需安装 Python（EXE 已自包含） |
| PowerShell | 5.1 或更高版本（系统内置） |

---

## 使用方法

### 归档会话

1. 在 Claude CLI 结束会话时，终端会显示类似内容：
   ```
   Resume this session with:
   claude --resume 3664d770-8252-4fda-b35d-7bb621a186fa
   PS C:\Users\bob-vm\Documents\myproject>
   ```
2. 全选复制上述文字
3. 在应用中点击 **"从剪贴板粘贴"**，或手动粘贴到文本框后点击 **"保存内容"**
4. 记录自动出现在下方列表中

### 恢复会话

1. 在列表中点击目标记录（高亮选中）
2. 点击 **"执行选中"**
3. 自动弹出新的 PowerShell 窗口，已切换到对应目录并执行 `claude --resume ...`

### 调整列宽

将鼠标悬停在表头的列分隔线上，光标变为双向箭头后拖拽即可。

### 导出备份

点击 **"导出"**，在弹出的文件对话框中选择保存位置，生成 `.json` 备份文件。

### 导入备份

点击 **"导入"**，选择备份文件后选择导入方式：
- **合并**：追加新记录，自动跳过重复项
- **替换**：清空现有数据，完全替换为备份内容

---

## 开发与打包

### 环境要求

- Python 3.11+
- 依赖：`flet`, `pillow`

### 安装依赖

```bat
pip install flet pillow
```

### 打包 EXE

```bat
build.bat
```

或手动执行：

```bat
python generate_icon.py
flet pack main.py --name "Claude历史记录管理" --icon assets/icon.ico
```

输出文件位于 `dist\Claude历史记录管理.exe`。

---

## 数据文件位置

```
C:\Users\<用户名>\.claude_sessions.json
```

---

## 技术栈

- **UI 框架**：[Flet](https://flet.dev/) 0.84（基于 Flutter，Material Design 3）
- **主题色**：Teal `#006A60`
- **文件对话框 / 剪贴板**：PowerShell + `System.Windows.Forms`（无 tkinter 依赖）
- **打包**：PyInstaller（通过 `flet pack`）

---

---

# Claude Session Manager

A Windows desktop tool for archiving and quickly resuming Claude CLI sessions.

---

## Features

- **One-click archive**: Paste the `claude --resume <id>` and `PS C:\...>` output from Claude CLI — the app extracts the timestamp, directory, and resume command automatically
- **Instant search**: Filter records in real time by time, directory, or command keyword
- **One-click resume**: Select a record and click "Execute Selected" — a new PowerShell window opens, changes to the saved directory, and runs the resume command
- **Resizable columns**: Drag the column dividers in the table header to adjust column widths
- **Import / Export**: Back up the database to a JSON file, or merge/replace from a backup
- **Persistent storage**: Records are saved to `~/.claude_sessions.json` and survive across app restarts

---

## System Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10 / 11 (64-bit) |
| Runtime | No Python installation needed (EXE is self-contained) |
| PowerShell | 5.1 or later (built into Windows) |

---

## Usage

### Archiving a Session

1. When a Claude CLI session ends, the terminal displays something like:
   ```
   Resume this session with:
   claude --resume 3664d770-8252-4fda-b35d-7bb621a186fa
   PS C:\Users\bob-vm\Documents\myproject>
   ```
2. Select and copy that text
3. In the app, click **"Paste from Clipboard"**, or manually paste into the text box and click **"Save"**
4. The record appears instantly in the list below

### Resuming a Session

1. Click the desired record in the list to select it (highlighted)
2. Click **"Execute Selected"**
3. A new PowerShell window opens, already in the saved directory with `claude --resume ...` running

### Resizing Columns

Hover over a column divider in the table header — the cursor changes to a resize arrow. Drag left or right to adjust.

### Exporting a Backup

Click **"Export"** and choose a save location. A `.json` backup file is created.

### Importing a Backup

Click **"Import"** and select a backup file. Choose how to import:
- **Merge**: Append new records, automatically skipping duplicates
- **Replace**: Clear existing data and replace it entirely with the backup

---

## Development & Packaging

### Prerequisites

- Python 3.11+
- Dependencies: `flet`, `pillow`

### Install Dependencies

```bat
pip install flet pillow
```

### Build EXE

```bat
build.bat
```

Or manually:

```bat
python generate_icon.py
flet pack main.py --name "Claude历史记录管理" --icon assets/icon.ico
```

Output: `dist\Claude历史记录管理.exe`

---

## Data File Location

```
C:\Users\<username>\.claude_sessions.json
```

---

## Tech Stack

- **UI Framework**: [Flet](https://flet.dev/) 0.84 (Flutter-based, Material Design 3)
- **Primary Color**: Teal `#006A60`
- **File Dialogs / Clipboard**: PowerShell + `System.Windows.Forms` (no tkinter dependency)
- **Packaging**: PyInstaller via `flet pack`
