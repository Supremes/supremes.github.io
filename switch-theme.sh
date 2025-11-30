#!/bin/bash
# Hexo 主题切换脚本
# 用于在 AnZhiYu 和 Butterfly 主题之间快速切换

CONFIG_FILE="_config.yml"

# 获取当前主题
current_theme=$(grep "^theme:" $CONFIG_FILE | awk '{print $2}')

echo "当前主题: $current_theme"
echo ""
echo "可用主题:"
echo "1. anzhiyu"
echo "2. butterfly"
echo ""

if [ -z "$1" ]; then
    read -p "请选择要切换的主题 (1/2 或直接输入主题名): " choice
else
    choice=$1
fi

case $choice in
    1|anzhiyu)
        new_theme="anzhiyu"
        ;;
    2|butterfly)
        new_theme="butterfly"
        ;;
    *)
        echo "无效的选择，退出脚本"
        exit 1
        ;;
esac

if [ "$current_theme" == "$new_theme" ]; then
    echo "已经是 $new_theme 主题了，无需切换"
    exit 0
fi

# 备份当前配置文件
cp $CONFIG_FILE ${CONFIG_FILE}.backup

# 使用 sed 替换主题配置
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^theme:.*$/theme: $new_theme/" $CONFIG_FILE
else
    # Linux
    sed -i "s/^theme:.*$/theme: $new_theme/" $CONFIG_FILE
fi

echo ""
echo "✓ 主题已切换为: $new_theme"
echo "✓ 原配置文件已备份为: ${CONFIG_FILE}.backup"
echo ""
echo "对应的主题配置文件:"
if [ "$new_theme" == "anzhiyu" ]; then
    echo "  - _config.anzhiyu.yml"
else
    echo "  - _config.butterfly.yml"
fi
echo ""
echo "运行以下命令以查看效果:"
echo "  hexo clean && hexo generate && hexo server"
