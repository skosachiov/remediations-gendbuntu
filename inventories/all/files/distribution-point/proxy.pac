function FindProxyForURL(url, host) {
    if (shExpMatch(host, '*.si.mi')) {
        return 'DIRECT';
    }
    if (isInNet(host, '10.0.0.0', '255.0.0.0')) {
        return 'DIRECT';
    }
    return 'PROXY proxy.si.mi:3128';
}