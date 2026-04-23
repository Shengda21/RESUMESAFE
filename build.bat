@echo off
chcp 65001 > nul
echo ========================================
echo  Claude 历史记录管理 - 打包 EXE（Flet）
echo ========================================

where python >nul 2>&1
if errorlevel 1 ( echo [错误] 未找到 Python & pause & exit /b 1 )

echo [1/4] 安装依赖...
pip install flet pillow --quiet

echo [2/4] 生成图标...
python generate_icon.py

echo [3/4] 打包中，请稍候...
flet pack main.py --name "Claude历史记录管理" --icon assets/icon.ico

if exist "dist\Claude历史记录管理.exe" (
    echo.
    echo [4/4] 打包成功！
    echo EXE 位于：dist\Claude历史记录管理.exe
    explorer dist
) else (
    echo [错误] 打包失败，请检查上方输出
)
pause
