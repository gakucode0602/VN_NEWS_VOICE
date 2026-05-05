package com.pmq.vnnewsvoice.auth.helpers;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

@Component
public class CookieHelper {

  @Value("${app.auth.refresh-cookie.name:refreshToken}")
  private String refreshCookieName;

  @Value("${app.auth.refresh-cookie.path:/api/auth}")
  private String refreshCookiePath;

  @Value("${app.auth.refresh-cookie.secure:false}")
  private boolean refreshCookieSecure;

  @Value("${app.auth.refresh-cookie.http-only:true}")
  private boolean refreshCookieHttpOnly;

  @Value("${app.auth.refresh-cookie.same-site:Lax}")
  private String refreshCookieSameSite;

  @Value("${app.auth.refresh-cookie.domain:}")
  private String refreshCookieDomain;

  @Value("${app.auth.refresh-token.expiration-days:7}")
  private int refreshTokenExpirationDays;

  public String getRefreshCookieName() {
    return refreshCookieName;
  }

  public ResponseCookie createRefreshTokenCookie(String refreshToken) {
    ResponseCookie.ResponseCookieBuilder builder =
        ResponseCookie.from(refreshCookieName, refreshToken)
            .httpOnly(refreshCookieHttpOnly)
            .secure(refreshCookieSecure)
            .path(refreshCookiePath)
            .sameSite(refreshCookieSameSite)
            .maxAge(Duration.ofDays(refreshTokenExpirationDays));

    if (refreshCookieDomain != null && !refreshCookieDomain.isBlank()) {
      builder.domain(refreshCookieDomain);
    }

    return builder.build();
  }

  public ResponseCookie clearRefreshTokenCookie() {
    ResponseCookie.ResponseCookieBuilder builder =
        ResponseCookie.from(refreshCookieName, "")
            .httpOnly(refreshCookieHttpOnly)
            .secure(refreshCookieSecure)
            .path(refreshCookiePath)
            .sameSite(refreshCookieSameSite)
            .maxAge(Duration.ZERO);

    if (refreshCookieDomain != null && !refreshCookieDomain.isBlank()) {
      builder.domain(refreshCookieDomain);
    }

    return builder.build();
  }
}
