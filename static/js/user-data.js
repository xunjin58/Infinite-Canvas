(function () {
    async function importLegacyData() {
        try {
            const response = await fetch('/api/user-data/import-dialog', { method: 'POST' });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.detail || '导入失败');
            if (result.cancelled) return;
            alert('旧数据已导入。页面将重新加载。');
            window.location.reload();
        } catch (error) {
            alert(`导入旧数据失败：${error.message || error}`);
        }
    }

    async function offerFirstRunImport() {
        try {
            const response = await fetch('/api/user-data/status', { cache: 'no-store' });
            const status = await response.json();
            if (status.first_run && window.confirm('检测到首次启动。要导入旧 Infinite Canvas 项目数据吗？')) {
                await importLegacyData();
            }
        } catch (_) {
            // A missing optional onboarding endpoint must not block the app.
        }
    }

    window.importLegacyInfiniteCanvasData = importLegacyData;
    window.addEventListener('DOMContentLoaded', offerFirstRunImport, { once: true });
})();
