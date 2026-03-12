async (page) => {
  const config = {
    targetUrl: "",
    quietWindowMs: 1000,
  };

  if (config.targetUrl) {
    await page.goto(config.targetUrl, { waitUntil: "load" });
  }

  await page.waitForLoadState("load").catch(() => {});
  await page.waitForTimeout(config.quietWindowMs);

  const metrics = await page.evaluate(async () => {
    return await new Promise((resolve) => {
      const result = {
        navigation: {
          ttfb: null,
          domContentLoaded: null,
          loadComplete: null,
        },
        paint: {
          fcp: null,
          lcp: null,
          cls: 0,
        },
        responsiveness: {
          tbtApprox: 0,
          longTaskCount: 0,
          ttiApprox: null,
        },
      };

      const navEntry = performance.getEntriesByType("navigation")[0];
      if (navEntry) {
        result.navigation.ttfb = Math.round(navEntry.responseStart - navEntry.requestStart);
        result.navigation.domContentLoaded = Math.round(navEntry.domContentLoadedEventEnd);
        result.navigation.loadComplete = Math.round(navEntry.loadEventEnd);
        result.responsiveness.ttiApprox = Math.round(navEntry.domInteractive);
      }

      for (const paintEntry of performance.getEntriesByType("paint")) {
        if (paintEntry.name === "first-contentful-paint") {
          result.paint.fcp = Math.round(paintEntry.startTime);
        }
      }

      const finish = () => {
        resolve({
          ...result,
          url: window.location.href,
          title: document.title,
        });
      };

      if (typeof PerformanceObserver === "undefined") {
        finish();
        return;
      }

      let observersClosed = false;
      const disconnectAll = () => {
        if (observersClosed) return;
        observersClosed = true;
        lcpObserver?.disconnect();
        clsObserver?.disconnect();
        longTaskObserver?.disconnect();
      };

      let lcpObserver = null;
      let clsObserver = null;
      let longTaskObserver = null;

      try {
        lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            result.paint.lcp = Math.round(lastEntry.startTime);
          }
        });
        lcpObserver.observe({ type: "largest-contentful-paint", buffered: true });
      } catch (error) {
        result.paint.lcp = result.paint.lcp;
      }

      try {
        clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              result.paint.cls += entry.value;
            }
          }
        });
        clsObserver.observe({ type: "layout-shift", buffered: true });
      } catch (error) {
        result.paint.cls = result.paint.cls;
      }

      try {
        longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            result.responsiveness.longTaskCount += 1;
            result.responsiveness.tbtApprox += Math.max(0, Math.round(entry.duration - 50));
          }
        });
        longTaskObserver.observe({ type: "longtask", buffered: true });
      } catch (error) {
        result.responsiveness.longTaskCount = result.responsiveness.longTaskCount;
      }

      window.setTimeout(() => {
        disconnectAll();
        result.paint.cls = Number(result.paint.cls.toFixed(4));
        finish();
      }, 1000);
    });
  });

  return metrics;
};
