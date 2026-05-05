package com.pmq.vnnewsvoice.auth.service;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

/**
 * Per-username login rate limiter using Bucket4j token-bucket algorithm.
 *
 * <p>Limit: 10 attempts per minute per username. This protects against brute-force attacks even
 * when the attacker rotates IP addresses (complementing nginx's per-IP limit).
 */
@Service
public class LoginRateLimiterService {

  private static final int MAX_ATTEMPTS = 10;
  private static final Duration REFILL_PERIOD = Duration.ofMinutes(1);

  private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();

  /**
   * Try to consume one token for the given username.
   *
   * @return true if the attempt is allowed, false if the rate limit is exceeded.
   */
  public boolean tryConsume(String username) {
    Bucket bucket = buckets.computeIfAbsent(username, this::newBucket);
    return bucket.tryConsume(1);
  }

  private Bucket newBucket(String username) {
    Bandwidth limit =
        Bandwidth.builder()
            .capacity(MAX_ATTEMPTS)
            .refillGreedy(MAX_ATTEMPTS, REFILL_PERIOD)
            .build();
    return Bucket.builder().addLimit(limit).build();
  }
}
