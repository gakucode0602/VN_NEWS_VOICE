package com.pmq.vnnewsvoice.auth.utils;

import com.nimbusds.jose.*;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jose.crypto.RSASSAVerifier;
import com.nimbusds.jose.jwk.KeyUse;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.text.ParseException;
import java.util.Base64;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

@Component
public class JwtUtils {

  private static final int FALLBACK_RSA_KEY_SIZE = 2048;

  @Value("${app.jwt.legacy-secret:}")
  private String jwtSecret;

  @Value("${app.jwt.expiration-ms:900000}")
  private int jwtExpiration;

  @Value("${app.jwt.issuer:vnnewsvoice-auth-service}")
  private String jwtIssuer;

  @Value("${app.jwt.audience:vnnewsvoice-services}")
  private String jwtAudience;

  @Value("${app.jwt.key-id:vnnewsvoice-auth-rs256-k1}")
  private String jwtKeyId;

  @Value("${app.jwt.rsa-private-key-base64:}")
  private String jwtPrivateKeyBase64;

  @Value("${app.jwt.rsa-public-key-base64:}")
  private String jwtPublicKeyBase64;

  @Value("${app.jwt.allow-legacy-hs256:true}")
  private boolean allowLegacyHs256;

  @Value("${app.jwt.verify-issuer-audience:true}")
  private boolean verifyIssuerAudience;

  private RSAPrivateKey signingPrivateKey;
  private RSAPublicKey signingPublicKey;

  @PostConstruct
  public void initializeSigningKeys() {
    try {
      if (!loadRsaKeysFromConfig()) {
        generateEphemeralRsaKeys();
      }
    } catch (Exception e) {
      throw new IllegalStateException("Cannot initialize RSA signing keys", e);
    }
  }

  public String generateJwtToken(Authentication authentication) {
    try {
      CustomUserDetails userPrincipal = (CustomUserDetails) authentication.getPrincipal();
      Date now = new Date();
      JWTClaimsSet claimsSet =
          new JWTClaimsSet.Builder()
              .issuer(jwtIssuer)
              .audience(List.of(jwtAudience))
              .subject(userPrincipal.getUsername())
              .claim("userId", userPrincipal.getUserInfo().getId())
              .claim("role", userPrincipal.getUserInfo().getRoleId().getName())
              .issueTime(now)
              .notBeforeTime(now)
              .jwtID(UUID.randomUUID().toString())
              .expirationTime(new Date(System.currentTimeMillis() + jwtExpiration))
              .build();

      JWSHeader header =
          new JWSHeader.Builder(JWSAlgorithm.RS256)
              .keyID(jwtKeyId)
              .type(JOSEObjectType.JWT)
              .build();
      SignedJWT signedJWT = new SignedJWT(header, claimsSet);
      signedJWT.sign(new RSASSASigner(signingPrivateKey));
      return signedJWT.serialize();

    } catch (JOSEException e) {
      System.err.println("Error generating JWT token: " + e.getMessage());
      return null;
    }
  }

  public String getUserNameFromJwtToken(String token) {
    try {
      return SignedJWT.parse(token).getJWTClaimsSet().getSubject();
    } catch (ParseException e) {
      System.err.println("Error parsing JWT token: " + e.getMessage());
      return null;
    }
  }

  public boolean validateJwtToken(String authToken) {
    try {
      SignedJWT signedJWT = SignedJWT.parse(authToken);
      if (!verifySignature(signedJWT)) {
        return false;
      }

      return validateClaims(signedJWT.getJWTClaimsSet());
    } catch (ParseException | JOSEException e) {
      System.err.println("Invalid JWT token: " + e.getMessage());
      return false;
    }
  }

  public RSAKey getPublicRsaJwk() {
    return new RSAKey.Builder(signingPublicKey)
        .keyID(jwtKeyId)
        .keyUse(KeyUse.SIGNATURE)
        .algorithm(JWSAlgorithm.RS256)
        .build();
  }

  public String getJwksEtag() {
    try {
      return "\"" + getPublicRsaJwk().computeThumbprint().toString() + "\"";
    } catch (JOSEException e) {
      return "\"" + jwtKeyId + "\"";
    }
  }

  private boolean validateClaims(JWTClaimsSet claimsSet) {
    Date now = new Date();
    Date expirationTime = claimsSet.getExpirationTime();
    if (expirationTime == null || expirationTime.before(now)) {
      return false;
    }

    Date notBeforeTime = claimsSet.getNotBeforeTime();
    if (notBeforeTime != null && notBeforeTime.after(now)) {
      return false;
    }

    if (claimsSet.getIssueTime() == null || claimsSet.getSubject() == null) {
      return false;
    }

    if (claimsSet.getClaim("userId") == null || claimsSet.getClaim("role") == null) {
      return false;
    }

    if (!verifyIssuerAudience) {
      return true;
    }

    if (!jwtIssuer.equals(claimsSet.getIssuer())) {
      return false;
    }

    return claimsSet.getAudience() != null
        && claimsSet.getAudience().stream().anyMatch(jwtAudience::equals);
  }

  private boolean verifySignature(SignedJWT signedJWT) throws JOSEException {
    JWSAlgorithm algorithm = signedJWT.getHeader().getAlgorithm();

    if (JWSAlgorithm.RS256.equals(algorithm)) {
      return signedJWT.verify(new RSASSAVerifier(signingPublicKey));
    }

    if (JWSAlgorithm.HS256.equals(algorithm)
        && allowLegacyHs256
        && jwtSecret != null
        && !jwtSecret.isBlank()) {
      JWSVerifier verifier = new MACVerifier(jwtSecret.getBytes(StandardCharsets.UTF_8));
      return signedJWT.verify(verifier);
    }

    return false;
  }

  private boolean loadRsaKeysFromConfig() throws Exception {
    if (jwtPrivateKeyBase64 == null
        || jwtPrivateKeyBase64.isBlank()
        || jwtPublicKeyBase64 == null
        || jwtPublicKeyBase64.isBlank()) {
      return false;
    }

    KeyFactory keyFactory = KeyFactory.getInstance("RSA");
    byte[] privateKeyBytes = decodeKeyMaterial(jwtPrivateKeyBase64);
    byte[] publicKeyBytes = decodeKeyMaterial(jwtPublicKeyBase64);

    signingPrivateKey =
        (RSAPrivateKey) keyFactory.generatePrivate(new PKCS8EncodedKeySpec(privateKeyBytes));
    signingPublicKey =
        (RSAPublicKey) keyFactory.generatePublic(new X509EncodedKeySpec(publicKeyBytes));
    return true;
  }

  private void generateEphemeralRsaKeys() throws Exception {
    KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
    generator.initialize(FALLBACK_RSA_KEY_SIZE);
    KeyPair keyPair = generator.generateKeyPair();
    signingPrivateKey = (RSAPrivateKey) keyPair.getPrivate();
    signingPublicKey = (RSAPublicKey) keyPair.getPublic();

    System.err.println(
        "JWT RSA keys are not configured. Generated ephemeral RSA key pair for current runtime only.");
  }

  private byte[] decodeKeyMaterial(String keyMaterial) {
    String normalized =
        keyMaterial
            .replace("-----BEGIN PRIVATE KEY-----", "")
            .replace("-----END PRIVATE KEY-----", "")
            .replace("-----BEGIN PUBLIC KEY-----", "")
            .replace("-----END PUBLIC KEY-----", "")
            .replaceAll("\\s+", "");
    return Base64.getDecoder().decode(normalized);
  }
}
