package com.pmq.vnnewsvoice.article.utils;

import static org.assertj.core.api.Assertions.assertThat;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

class JwtUtilsTest {

  private static final String HS256_SECRET = "0123456789abcdef0123456789abcdef";
  private static final String ISSUER = "vnnewsvoice-test-issuer";
  private static final String AUDIENCE = "vnnewsvoice-test-audience";

  @Test
  void validateJwtTokenShouldAcceptLegacyHs256WhenConfigured() throws Exception {
    JwtUtils jwtUtils = new JwtUtils();
    ReflectionTestUtils.setField(jwtUtils, "jwtSecret", HS256_SECRET);
    ReflectionTestUtils.setField(jwtUtils, "allowLegacyHs256", true);
    ReflectionTestUtils.setField(jwtUtils, "verifyIssuerAudience", true);
    ReflectionTestUtils.setField(jwtUtils, "jwtIssuer", ISSUER);
    ReflectionTestUtils.setField(jwtUtils, "jwtAudience", AUDIENCE);

    String token = createLegacyToken();

    assertThat(jwtUtils.validateJwtToken(token)).isTrue();
    assertThat(jwtUtils.getUsernameFromJwtToken(token)).isEqualTo("reader@example.com");
    assertThat(jwtUtils.getUserIdFromJwtToken(token)).isEqualTo(123L);
    assertThat(jwtUtils.getRoleFromJwtToken(token)).isEqualTo("READER");
  }

  @Test
  void invalidTokenShouldBeRejected() {
    JwtUtils jwtUtils = new JwtUtils();

    assertThat(jwtUtils.validateJwtToken("invalid-token")).isFalse();
    assertThat(jwtUtils.getUsernameFromJwtToken("invalid-token")).isNull();
    assertThat(jwtUtils.getUserIdFromJwtToken("invalid-token")).isNull();
    assertThat(jwtUtils.getRoleFromJwtToken("invalid-token")).isNull();
  }

  private String createLegacyToken() throws Exception {
    Date now = new Date();

    JWTClaimsSet claimsSet =
        new JWTClaimsSet.Builder()
            .issuer(ISSUER)
            .audience(List.of(AUDIENCE))
            .subject("reader@example.com")
            .claim("userId", 123L)
            .claim("role", "READER")
            .issueTime(now)
            .notBeforeTime(new Date(now.getTime() - 1_000))
            .expirationTime(new Date(now.getTime() + 60_000))
            .build();

    SignedJWT signedJWT = new SignedJWT(new JWSHeader(JWSAlgorithm.HS256), claimsSet);
    signedJWT.sign(new MACSigner(HS256_SECRET.getBytes(StandardCharsets.UTF_8)));
    return signedJWT.serialize();
  }
}
