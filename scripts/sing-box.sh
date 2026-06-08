#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  sing-box + VLESS Reality 一键管理脚本
# ============================================================

INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/sing-box"
CONFIG_FILE="${CONFIG_DIR}/config.json"
SERVICE_FILE="/etc/systemd/system/sing-box.service"
GITHUB_REPO="SagerNet/sing-box"
MIRROR_PREFIX="https://ghfast.top"

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---------- 前置检查 ----------
check_root() {
    [[ $EUID -eq 0 ]] || error "请使用 root 用户运行此脚本"
}

check_os() {
    [[ "$(uname -s)" == "Linux" ]] || error "仅支持 Linux 系统"
}

get_arch() {
    case "$(uname -m)" in
        x86_64)  echo "amd64" ;;
        aarch64) echo "arm64" ;;
        *)       error "不支持的架构: $(uname -m)" ;;
    esac
}

is_installed() {
    [[ -f "${INSTALL_DIR}/sing-box" ]] && [[ -f "${CONFIG_FILE}" ]]
}

get_ip() {
    local ip
    ip=$(curl -s4 --connect-timeout 5 https://api.ipify.org 2>/dev/null) ||
    ip=$(curl -s4 --connect-timeout 5 https://ifconfig.me 2>/dev/null) ||
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    echo "${ip}"
}

# ---------- 下载 ----------
get_latest_version() {
    local ver
    ver=$(curl -s --connect-timeout 10 "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    if [[ -z "$ver" ]]; then
        ver=$(curl -s --connect-timeout 10 "${MIRROR_PREFIX}/https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    fi
    [[ -n "$ver" ]] || error "无法获取最新版本号"
    echo "$ver"
}

download_file() {
    local url="$1" dest="$2"
    info "下载: ${url}"
    if curl -sL --connect-timeout 15 --max-time 120 -o "$dest" "$url" && [[ -s "$dest" ]]; then
        return 0
    fi
    local mirror_url="${MIRROR_PREFIX}/${url}"
    warn "直连下载失败，尝试镜像: ${mirror_url}"
    if curl -sL --connect-timeout 15 --max-time 120 -o "$dest" "$mirror_url" && [[ -s "$dest" ]]; then
        return 0
    fi
    rm -f "$dest"
    return 1
}

# ---------- 安装 ----------
do_install() {
    if is_installed; then
        warn "sing-box 已安装"
        read -rp "是否覆盖安装？[y/N]: " confirm
        [[ "$confirm" =~ ^[Yy]$ ]] || return
        systemctl stop sing-box 2>/dev/null || true
    fi

    local arch ver
    arch=$(get_arch)
    info "检测架构: ${arch}"

    ver=$(get_latest_version)
    info "最新版本: ${ver}"

    local filename="sing-box-${ver#v}-linux-${arch}"
    local url="https://github.com/${GITHUB_REPO}/releases/download/${ver}/${filename}.tar.gz"
    local tmpdir
    tmpdir=$(mktemp -d)

    download_file "$url" "${tmpdir}/sing-box.tar.gz" || error "下载 sing-box 失败"

    tar xzf "${tmpdir}/sing-box.tar.gz" -C "$tmpdir"
    cp "${tmpdir}/${filename}/sing-box" "${INSTALL_DIR}/sing-box"
    chmod +x "${INSTALL_DIR}/sing-box"
    rm -rf "$tmpdir"
    info "sing-box ${ver} 安装完成"

    # 生成密钥
    local keypair uuid short_id private_key public_key
    keypair=$(sing-box generate reality-keypair)
    private_key=$(echo "$keypair" | grep PrivateKey | awk '{print $2}')
    public_key=$(echo "$keypair" | grep PublicKey | awk '{print $2}')
    uuid=$(sing-box generate uuid)
    short_id=$(openssl rand -hex 8)

    # 交互选择参数
    echo ""
    echo -e "${CYAN}--- 配置参数 ---${NC}"

    read -rp "监听端口 [默认 443]: " port
    port=${port:-443}

    echo "SNI 目标站点:"
    echo "  1) www.apple.com (默认)"
    echo "  2) www.microsoft.com"
    echo "  3) www.samsung.com"
    echo "  4) 自定义"
    read -rp "选择 [1-4]: " sni_choice
    case "${sni_choice}" in
        2) sni="www.microsoft.com" ;;
        3) sni="www.samsung.com" ;;
        4) read -rp "输入 SNI: " sni ;;
        *) sni="www.apple.com" ;;
    esac

    # 写入配置
    mkdir -p "${CONFIG_DIR}"
    cat > "${CONFIG_FILE}" << CFGEOF
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": ${port},
      "users": [
        {
          "uuid": "${uuid}",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "${sni}",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "${sni}",
            "server_port": 443
          },
          "private_key": "${private_key}",
          "short_id": ["${short_id}"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ]
}
CFGEOF

    sing-box check -c "${CONFIG_FILE}" || error "配置校验失败"
    info "配置写入 ${CONFIG_FILE}"

    # systemd 服务
    cat > "${SERVICE_FILE}" << 'SVCEOF'
[Unit]
Description=sing-box service
Documentation=https://sing-box.sagernet.org
After=network.target nss-lookup.target

[Service]
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=10
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable sing-box
    systemctl start sing-box

    if systemctl is-active --quiet sing-box; then
        info "sing-box 启动成功"
    else
        error "sing-box 启动失败，请检查日志: journalctl -u sing-box"
    fi

    echo ""
    show_connection_info
}

# ---------- 卸载 ----------
do_uninstall() {
    is_installed || { warn "sing-box 未安装"; return; }
    read -rp "确定卸载 sing-box？[y/N]: " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || return

    systemctl stop sing-box 2>/dev/null || true
    systemctl disable sing-box 2>/dev/null || true
    rm -f "${SERVICE_FILE}"
    rm -f "${INSTALL_DIR}/sing-box"
    rm -rf "${CONFIG_DIR}"
    systemctl daemon-reload

    info "sing-box 已卸载"
}

# ---------- 连接信息 ----------
show_connection_info() {
    is_installed || { warn "sing-box 未安装"; return; }

    local ip port uuid sni public_key short_id private_key
    ip=$(get_ip)

    port=$(grep -o '"listen_port": *[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*')
    uuid=$(grep -o '"uuid": *"[^"]*"' "$CONFIG_FILE" | head -1 | cut -d'"' -f4)
    sni=$(grep -o '"server_name": *"[^"]*"' "$CONFIG_FILE" | head -1 | cut -d'"' -f4)
    private_key=$(grep -o '"private_key": *"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
    short_id=$(grep -o '"short_id": *\["[^"]*"\]' "$CONFIG_FILE" | grep -o '"[^"]*"' | tail -1 | tr -d '"')

    # 从 private_key 反推 public_key
    public_key=$(sing-box generate reality-keypair --private-key "$private_key" 2>/dev/null | grep PublicKey | awk '{print $2}')
    if [[ -z "$public_key" ]]; then
        public_key="<需从安装时记录获取>"
    fi

    local link="vless://${uuid}@${ip}:${port}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=${sni}&fp=chrome&pbk=${public_key}&sid=${short_id}&type=tcp#sing-box-reality"

    echo ""
    echo -e "${BOLD}${CYAN}============ 连接信息 ============${NC}"
    echo -e " 协议:       ${GREEN}VLESS${NC}"
    echo -e " 地址:       ${GREEN}${ip}${NC}"
    echo -e " 端口:       ${GREEN}${port}${NC}"
    echo -e " UUID:       ${GREEN}${uuid}${NC}"
    echo -e " 流控:       ${GREEN}xtls-rprx-vision${NC}"
    echo -e " 安全:       ${GREEN}Reality${NC}"
    echo -e " SNI:        ${GREEN}${sni}${NC}"
    echo -e " 公钥:       ${GREEN}${public_key}${NC}"
    echo -e " Short ID:   ${GREEN}${short_id}${NC}"
    echo -e " 指纹:       ${GREEN}chrome${NC}"
    echo -e "${BOLD}${CYAN}==================================${NC}"
    echo ""
    echo -e "${BOLD}分享链接:${NC}"
    echo -e "${YELLOW}${link}${NC}"
    echo ""
}

# ---------- 服务管理 ----------
do_service() {
    is_installed || { warn "sing-box 未安装"; return; }

    echo ""
    echo "  1) 启动"
    echo "  2) 停止"
    echo "  3) 重启"
    echo "  4) 查看状态"
    echo "  0) 返回"
    read -rp "选择 [0-4]: " choice

    case "$choice" in
        1) systemctl start sing-box   && info "已启动" ;;
        2) systemctl stop sing-box    && info "已停止" ;;
        3) systemctl restart sing-box && info "已重启" ;;
        4) systemctl status sing-box --no-pager ;;
        0) return ;;
        *) warn "无效选项" ;;
    esac
}

# ---------- 升级 ----------
do_upgrade() {
    is_installed || { warn "sing-box 未安装"; return; }

    local current_ver new_ver arch
    current_ver=$(sing-box version 2>/dev/null | head -1 | awk '{print $NF}')
    new_ver=$(get_latest_version)

    if [[ "v${current_ver}" == "${new_ver}" ]]; then
        info "已是最新版本: ${current_ver}"
        return
    fi

    info "当前版本: ${current_ver} → 最新版本: ${new_ver}"
    read -rp "确定升级？[y/N]: " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || return

    arch=$(get_arch)
    local filename="sing-box-${new_ver#v}-linux-${arch}"
    local url="https://github.com/${GITHUB_REPO}/releases/download/${new_ver}/${filename}.tar.gz"
    local tmpdir
    tmpdir=$(mktemp -d)

    download_file "$url" "${tmpdir}/sing-box.tar.gz" || error "下载失败"

    systemctl stop sing-box
    tar xzf "${tmpdir}/sing-box.tar.gz" -C "$tmpdir"
    cp "${tmpdir}/${filename}/sing-box" "${INSTALL_DIR}/sing-box"
    chmod +x "${INSTALL_DIR}/sing-box"
    rm -rf "$tmpdir"
    systemctl start sing-box

    info "升级完成: $(sing-box version | head -1)"
}

# ---------- 日志 ----------
do_logs() {
    is_installed || { warn "sing-box 未安装"; return; }
    journalctl -u sing-box --no-pager -n 50
}

# ---------- 主菜单 ----------
show_menu() {
    local status_text
    if is_installed && systemctl is-active --quiet sing-box; then
        status_text="${GREEN}运行中${NC}"
    elif is_installed; then
        status_text="${YELLOW}已停止${NC}"
    else
        status_text="${RED}未安装${NC}"
    fi

    echo ""
    echo -e "${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}  sing-box VLESS Reality 管理脚本${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    echo -e "  状态: ${status_text}"
    if is_installed; then
        echo -e "  版本: $(sing-box version 2>/dev/null | head -1 | awk '{print $NF}')"
    fi
    echo -e "${CYAN}----------------------------------------${NC}"
    echo "  1) 安装 sing-box"
    echo "  2) 卸载 sing-box"
    echo "  3) 查看连接信息"
    echo "  4) 服务管理"
    echo "  5) 升级 sing-box"
    echo "  6) 查看日志"
    echo "  0) 退出"
    echo -e "${CYAN}----------------------------------------${NC}"
}

main() {
    check_root
    check_os

    # 支持命令行直接调用
    case "${1:-}" in
        install)   do_install;   exit ;;
        uninstall) do_uninstall; exit ;;
        info)      show_connection_info; exit ;;
        upgrade)   do_upgrade;   exit ;;
        logs)      do_logs;      exit ;;
        *) ;;
    esac

    while true; do
        show_menu
        read -rp "  选择 [0-6]: " choice
        case "$choice" in
            1) do_install ;;
            2) do_uninstall ;;
            3) show_connection_info ;;
            4) do_service ;;
            5) do_upgrade ;;
            6) do_logs ;;
            0) echo "再见"; exit 0 ;;
            *) warn "无效选项" ;;
        esac
    done
}

main "$@"
