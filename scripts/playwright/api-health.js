async (page) => {
  const config = {
    frontendBaseUrl: "http://localhost:3000",
    backendBaseUrl: "http://localhost:8000",
    auth: {
      mode: "public-only",
      provider: "google",
      credentials: {
        email: "",
        password: "",
      },
    },
    publicEndpoints: [
      { method: "GET", path: "/health" },
      { method: "GET", path: "/api/openapi.json" },
    ],
    protectedEndpoints: [
      { method: "GET", path: "/api/v1/profile/me" },
      { method: "GET", path: "/api/v1/roadmaps" },
      { method: "GET", path: "/api/v1/actionkits/laws" },
      { method: "GET", path: "/api/v1/actionkits/kits" },
    ],
  };

  const requestEndpoint = async (endpoint, headers = {}) => {
    const method = endpoint.method.toLowerCase();
    const response = await page.request[method](`${config.backendBaseUrl}${endpoint.path}`, { headers });
    return {
      ...endpoint,
      status: response.status(),
      ok: response.ok(),
      contentType: response.headers()["content-type"] || null,
    };
  };

  const results = {
    mode: "public-only",
    public: [],
    protected: [],
  };

  for (const endpoint of config.publicEndpoints) {
    results.public.push(await requestEndpoint(endpoint));
  }

  if (config.auth.mode === "public-only") {
    results.protected.push({
      skipped: true,
      reason: "auth.mode is public-only",
      paths: config.protectedEndpoints.map((endpoint) => endpoint.path),
    });
    return results;
  }

  const applyAuthPayload = async (payload) => {
    const storedUser = {
      id: String(payload.user.id),
      username: payload.user.full_name || payload.user.email.split("@")[0] || payload.user.email,
      email: payload.user.email,
      full_name: payload.user.full_name || undefined,
      is_superuser: Boolean(payload.user.is_superuser),
    };

    await page.goto(`${config.frontendBaseUrl}/login`, { waitUntil: "domcontentloaded" });
    await page.evaluate((authPayload) => {
      window.localStorage.setItem("token", authPayload.access_token);
      if (authPayload.refresh_token) {
        window.localStorage.setItem("refresh_token", authPayload.refresh_token);
      }
      if (authPayload.current_team_id) {
        window.localStorage.setItem("current_team_id", authPayload.current_team_id);
      }
      window.localStorage.setItem("user", JSON.stringify(authPayload.user));
    }, { ...payload, user: storedUser });
    await page.goto(`${config.frontendBaseUrl}/dashboard`, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle").catch(() => {});
  };

  if (config.auth.mode === "credentials") {
    const canLogin = Boolean(config.auth.credentials.email && config.auth.credentials.password);
    if (!canLogin) {
      results.protected.push({
        skipped: true,
        reason: "credentials missing",
        paths: config.protectedEndpoints.map((endpoint) => endpoint.path),
      });
      return results;
    }

    await page.goto(`${config.frontendBaseUrl}/login`, { waitUntil: "domcontentloaded" });
    await page.getByTestId("login-email").fill(config.auth.credentials.email);
    await page.getByTestId("login-password").fill(config.auth.credentials.password);
    await page.getByTestId("login-submit").click();
    await page.waitForURL("**/dashboard", { timeout: 10000 }).catch(() => {});
    await page.waitForLoadState("networkidle").catch(() => {});
    results.mode = "credentials";
  } else if (config.auth.mode === "social-mock") {
    const response = await page.request.post(
      `${config.backendBaseUrl}/api/v1/auth/login/social/${config.auth.provider}`
    );
    if (!response.ok()) {
      results.protected.push({
        loginAttempted: true,
        loginSucceeded: false,
        provider: config.auth.provider,
        status: response.status(),
      });
      return results;
    }

    const payload = await response.json();
    await applyAuthPayload(payload);
    results.mode = "social-mock";
  } else {
    results.protected.push({
      skipped: true,
      reason: `unsupported auth mode: ${config.auth.mode}`,
      paths: config.protectedEndpoints.map((endpoint) => endpoint.path),
    });
    return results;
  }

  const auth = await page.evaluate(() => ({
    token: window.localStorage.getItem("token"),
    teamId: window.localStorage.getItem("current_team_id"),
  }));
  const headers = {
    ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
    ...(auth.teamId ? { "X-Team-Id": auth.teamId } : {}),
  };

  for (const endpoint of config.protectedEndpoints) {
    results.protected.push(await requestEndpoint(endpoint, headers));
  }

  return {
    ...results,
    auth: {
      hasToken: Boolean(auth.token),
      hasTeamId: Boolean(auth.teamId),
    },
  };
};
