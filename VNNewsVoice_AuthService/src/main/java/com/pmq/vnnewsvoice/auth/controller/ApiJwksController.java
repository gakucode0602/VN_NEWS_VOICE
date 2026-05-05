package com.pmq.vnnewsvoice.auth.controller;

import com.nimbusds.jose.jwk.RSAKey;
import com.pmq.vnnewsvoice.auth.utils.JwtUtils;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/.well-known")
public class ApiJwksController {

  private final JwtUtils jwtUtils;

  @Value("${app.jwks.cache-control-max-age-seconds:300}")
  private long cacheControlMaxAgeSeconds;

  @GetMapping("/jwks.json")
  public ResponseEntity<Map<String, Object>> getJwks(
      @RequestHeader(name = HttpHeaders.IF_NONE_MATCH, required = false) String ifNoneMatch) {

    String etag = jwtUtils.getJwksEtag();
    CacheControl cacheControl =
        CacheControl.maxAge(cacheControlMaxAgeSeconds, TimeUnit.SECONDS).cachePublic();

    if (hasMatchingEtag(ifNoneMatch, etag)) {
      return ResponseEntity.status(HttpStatus.NOT_MODIFIED)
          .cacheControl(cacheControl)
          .eTag(etag)
          .build();
    }

    RSAKey publicJwk = jwtUtils.getPublicRsaJwk();
    Map<String, Object> body = Map.of("keys", List.of(publicJwk.toPublicJWK().toJSONObject()));

    return ResponseEntity.ok().cacheControl(cacheControl).eTag(etag).body(body);
  }

  private boolean hasMatchingEtag(String ifNoneMatch, String etag) {
    if (ifNoneMatch == null || ifNoneMatch.isBlank()) {
      return false;
    }

    return Arrays.stream(ifNoneMatch.split(","))
        .map(String::trim)
        .anyMatch(candidate -> candidate.equals(etag) || candidate.equals("*"));
  }
}
