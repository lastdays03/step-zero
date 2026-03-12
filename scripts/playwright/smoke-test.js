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
    publicPages: ["/login"],
    authPages: ["/dashboard", "/roadmap", "/actionkit", "/growth-club", "/profile", "/settings"],
  };

  const results = {
    mode: "public-only",
    public: [],
    auth: [],
  };

  const collectConsoleErrors = () => {
    const errors = [];
    const handler = (message) => {
      if (message.type() === "error") {
        errors.push(message.text());
      }
    };
    page.on("console", handler);
    return {
      errors,
      dispose: () => page.off("console", handler),
    };
  };

  const visitPage = async (path) => {
    const tracker = collectConsoleErrors();
    const response = await page.goto(`${config.frontendBaseUrl}${path}`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForLoadState("networkidle").catch(() => {});
    const bodyText = await page.locator("body").textContent();
    const url = page.url();
    const title = await page.title();
    tracker.dispose();

    return {
      path,
      status: response?.status() ?? null,
      title,
      url,
      hasContent: Boolean(bodyText && bodyText.trim().length > 0),
      consoleErrors: tracker.errors.slice(0, 5),
    };
  };

  for (const path of config.publicPages) {
    results.public.push(await visitPage(path));
  }

  if (config.auth.mode === "public-only") {
    results.auth.push({
      skipped: true,
      reason: "auth.mode is public-only",
      paths: config.authPages,
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
      results.auth.push({
        skipped: true,
        reason: "credentials missing",
        paths: config.authPages,
      });
      return results;
    }

    results.mode = "credentials";
    await page.goto(`${config.frontendBaseUrl}/login`, { waitUntil: "domcontentloaded" });
    await page.getByTestId("login-email").fill(config.auth.credentials.email);
    await page.getByTestId("login-password").fill(config.auth.credentials.password);
    await page.getByTestId("login-submit").click();
    await page.waitForURL("**/dashboard", { timeout: 10000 }).catch(() => {});
    await page.waitForLoadState("networkidle").catch(() => {});
  } else if (config.auth.mode === "social-mock") {
    results.mode = "social-mock";
    const response = await page.request.post(
      `${config.backendBaseUrl}/api/v1/auth/login/social/${config.auth.provider}`
    );
    if (!response.ok()) {
      results.auth.push({
        loginAttempted: true,
        loginSucceeded: false,
        provider: config.auth.provider,
        status: response.status(),
      });
      return results;
    }

    const payload = await response.json();
    await applyAuthPayload(payload);
  } else {
    results.auth.push({
      skipped: true,
      reason: `unsupported auth mode: ${config.auth.mode}`,
      paths: config.authPages,
    });
    return results;
  }

  const authStorage = await page.evaluate(() => ({
    hasToken: Boolean(window.localStorage.getItem("token")),
    hasRefreshToken: Boolean(window.localStorage.getItem("refresh_token")),
    hasCurrentTeamId: Boolean(window.localStorage.getItem("current_team_id")),
  }));

  results.auth.push({
    path: "/login",
    loginAttempted: true,
    loginSucceeded: /\/dashboard(?:\/)?$/.test(page.url()),
    storage: authStorage,
  });

  for (const path of config.authPages) {
    results.auth.push(await visitPage(path));
  }

  return results;
};
