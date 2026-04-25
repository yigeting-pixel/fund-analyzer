#!/bin/bash

# 部署到Render.com的脚本
# 使用方法：在项目根目录运行 ./deploy-to-render.sh

echo "========================================"
echo "    基金分析工具 - 部署到Render.com"
echo "========================================"
echo ""

# 检查git是否初始化
if [ ! -d .git ]; then
    echo "🔧 初始化Git仓库..."
    git init
    echo "node_modules/" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo ".Python" >> .gitignore
    echo "venv/" >> .gitignore
    echo "env/" >> .gitignore
fi

# 检查是否已添加远程仓库
if ! git remote | grep -q "origin"; then
    echo "📦 请先在GitHub/GitLab创建仓库，然后："
    echo "   git remote add origin <你的仓库地址>"
    echo "   git push -u origin main"
    echo ""
    echo "🌐 然后访问 https://render.com/ 导入该仓库进行部署"
    echo ""
    echo "❗ 或者我可以帮你创建一个一键部署链接..."
    read -p "是否生成一键部署链接？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ 正在生成一键部署链接..."
        echo ""
        echo "🔗 一键部署链接："
        echo "https://render.com/deploy?repo=https://github.com/[YOUR_USERNAME]/fund-analyzer"
        echo ""
        echo "📝 使用说明："
        echo "1. 将上面的 [YOUR_USERNAME] 替换为你的GitHub用户名"
        echo "2. 在GitHub创建名为 'fund-analyzer' 的仓库"
        echo "3. 推送代码到GitHub："
        echo "   git add ."
        echo "   git commit -m 'Initial commit'"
        echo "   git push -u origin main"
        echo "4. 点击上面的链接，选择你的仓库进行部署"
        echo ""
    fi
else
    echo "📤 推送到远程仓库..."
    git add .
    git commit -m "Update fund analyzer" 2>/dev/null || echo "✅ 无需提交"
    git push origin main 2>/dev/null || echo "⚠️  请手动推送：git push origin main"

    echo ""
    echo "🌐 访问 https://render.com/ 查看部署状态"
    echo "部署完成后，你将获得一个可分享的链接！"
fi

echo ""
echo "💡 提示："
echo "- Render.com 免费额度足够个人使用"
echo "- 部署后你将获得一个 .onrender.com 结尾的链接"
echo "- 该链接可以在手机和任何设备上访问"
echo "========================================"