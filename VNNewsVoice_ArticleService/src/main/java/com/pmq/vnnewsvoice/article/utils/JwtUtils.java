package com.pmq.vnnewsvoice.article.utils;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSVerifier;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jose.jwk.source.JWKSource;
import com.nimbusds.jose.jwk.source.JWKSourceBuilder;
import com.nimbusds.jose.proc.BadJOSEException;
import com.nimbusds.jose.proc.JWSKeySelector;
import com.nimbusds.jose.proc.JWSVerificationKeySelector;
import com.nimbusds.jose.proc.SecurityContext;
import com.nimbusds.jose.util.DefaultResourceRetriever;
import com.nimbusds.jose.util.ResourceRetriever;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import com.nimbusds.jwt.proc.ConfigurableJWTProcessor;
import com.nimbusds.jwt.proc.DefaultJWTProcessor;
import jakarta.annotation.PostConstruct;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.ParseException;
import java.util.Date;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * JWT utility for ArticleService — verify only (no signing). JWT tokens are issued by AuthService;
 * this service only validates them.
 */
@Component
public class JwtUtils {

  @Value("${app.jwt.legacy-secret:}")
  private String jwtSecret;

  @Value("${app.auth.jwks-url:http://localhost:8084/api/.well-known/jwks.json}")
  private String authJwksUrl;

  @Value("${app.auth.jwks-connect-timeout-ms:2000}")
  private int authJwksConnectTimeoutMs;

  @Value("${app.auth.jwks-read-timeout-ms:2000}")
  private int authJwksReadTimeoutMs;

  @Value("${app.auth.jwks-cache-lifespan-seconds:900}")
  private long jwksCacheLifespanSeconds;

  @Value("${app.auth.jwks-cache-refresh-seconds:300}")
  private long jwksCacheRefreshSeconds;

  @Value("${app.jwt.issuer:vnnewsvoice-auth-service}")
  private String jwtIssuer;

  @Value("${app.jwt.audience:vnnewsvoice-services}")
  private String jwtAudience;

  @Value("${app.jwt.allow-legacy-hs256:true}")
  private boolean allowLegacyHs256;

  @Value("${app.jwt.verify-issuer-audience:true}")
  private boolean verifyIssuerAudience;

  private ConfigurableJWTProcessor<SecurityContext> jwtProcessor;

  @PostConstruct
  public void initialize() {
    initializeJwtProcessor();
  }

  public boolean validateJwtToken(String authToken) {
    try {
      SignedJWT signedJWT = SignedJWT.parse(authToken);

      JWTClaimsSet claims;
      JWSAlgorithm algorithm = signedJWT.getHeader().getAlgorithm();
      if (JWSAlgorithm.RS256.equals(algorithm)) {
        claims = validateRs256Token(authToken);
      } else if (JWSAlgorithm.HS256.equals(algorithm)) {
        claims = validateLegacyHs256Token(signedJWT);
      } else {
        return false;
      }

      if (claims == null) {
        return false;
      }

      return validateClaims(claims);
    } catch (ParseException | JOSEException e) {
      return false;
    }
  }

  public String getUsernameFromJwtToken(String token) {
    try {
      return SignedJWT.parse(token).getJWTClaimsSet().getSubject();
    } catch (ParseException e) {
      return null;
    }
  }

  public Long getUserIdFromJwtToken(String token) {
    try {
      JWTClaimsSet claims = SignedJWT.parse(token).getJWTClaimsSet();
      Object userIdClaim = claims.getClaim("userId");
      if (userIdClaim instanceof Number) {
        return ((Number) userIdClaim).longValue();
      }
      return null;
    } catch (ParseException e) {
      return null;
    }
  }

  public String getRoleFromJwtToken(String token) {
    try {
      JWTClaimsSet claims = SignedJWT.parse(token).getJWTClaimsSet();
      return (String) claims.getClaim("role");
    } catch (ParseException e) {
      return null;
    }
  }

  private synchronized void initializeJwtProcessor() {
    try {
      URI jwksUri = URI.create(authJwksUrl);
      URL jwksUrl = jwksUri.toURL();
      ResourceRetriever resourceRetriever =
          new DefaultResourceRetriever(authJwksConnectTimeoutMs, authJwksReadTimeoutMs);

      long jwksCacheLifespanMs = TimeUnit.SECONDS.toMillis(jwksCacheLifespanSeconds);
      long jwksCacheRefreshMs = TimeUnit.SECONDS.toMillis(jwksCacheRefreshSeconds);

      JWKSource<SecurityContext> jwkSource =
          JWKSourceBuilder.<SecurityContext>create(jwksUrl, resourceRetriever)
              .cache(jwksCacheLifespanMs, jwksCacheRefreshMs)
              .build();

      JWSKeySelector<SecurityContext> keySelector =
          new JWSVerificationKeySelector<>(JWSAlgorithm.RS256, jwkSource);
      DefaultJWTProcessor<SecurityContext> processor = new DefaultJWTProcessor<>();
      processor.setJWSKeySelector(keySelector);
      this.jwtProcessor = processor;
    } catch (IllegalArgumentException | MalformedURLException e) {
      throw new IllegalStateException("Invalid AUTH_JWKS_URL: " + authJwksUrl, e);
    }
  }

  private JWTClaimsSet validateRs256Token(String authToken) throws JOSEException {
    try {
      return jwtProcessor.process(authToken, null);
    } catch (BadJOSEException e) {
      initializeJwtProcessor();
      try {
        return jwtProcessor.process(authToken, null);
      } catch (BadJOSEException | ParseException retryException) {
        throw new JOSEException("RS256 token verification failed", retryException);
      }
    } catch (ParseException e) {
      throw new JOSEException("Cannot parse RS256 token", e);
    }
  }

  private JWTClaimsSet validateLegacyHs256Token(SignedJWT signedJWT)
      throws JOSEException, ParseException {
    if (!allowLegacyHs256 || jwtSecret == null || jwtSecret.isBlank()) {
      return null;
    }

    JWSVerifier verifier = new MACVerifier(jwtSecret.getBytes(StandardCharsets.UTF_8));
    if (!signedJWT.verify(verifier)) {
      return null;
    }

    return signedJWT.getJWTClaimsSet();
  }

  private boolean validateClaims(JWTClaimsSet claims) {
    Date now = new Date();
    Date expirationTime = claims.getExpirationTime();
    if (expirationTime == null || expirationTime.before(now)) {
      return false;
    }

    Date notBeforeTime = claims.getNotBeforeTime();
    if (notBeforeTime != null && notBeforeTime.after(now)) {
      return false;
    }

    if (claims.getIssueTime() == null
        || claims.getSubject() == null
        || claims.getSubject().isBlank()) {
      return false;
    }

    if (claims.getClaim("userId") == null || claims.getClaim("role") == null) {
      return false;
    }

    if (!verifyIssuerAudience) {
      return true;
    }

    if (!jwtIssuer.equals(claims.getIssuer())) {
      return false;
    }

    return claims.getAudience() != null
        && claims.getAudience().stream().anyMatch(jwtAudience::equals);
  }
}
