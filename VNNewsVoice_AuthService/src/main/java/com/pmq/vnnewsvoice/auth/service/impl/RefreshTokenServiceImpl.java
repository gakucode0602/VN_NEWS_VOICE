package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.RefreshToken;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.repository.RefreshTokenRepository;
import com.pmq.vnnewsvoice.auth.service.RefreshTokenService;
import java.util.Date;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class RefreshTokenServiceImpl implements RefreshTokenService {

  private final RefreshTokenRepository refreshTokenRepository;

  @Value("${REFRESH_TOKEN_EXPIRATION_DAYS}")
  private int refreshTokenExpirationDays;

  @Override
  @Transactional
  public RefreshToken createRefreshToken(UserInfo userInfo) {
    // Revoke all existing valid tokens for this user before creating a new one
    refreshTokenRepository.revokeAllByUserId(userInfo.getId());

    RefreshToken refreshToken = new RefreshToken();
    refreshToken.setToken(UUID.randomUUID().toString());
    refreshToken.setUserId(userInfo);
    refreshToken.setCreatedAt(new Date());
    refreshToken.setExpiresAt(
        new Date(
            System.currentTimeMillis() + (long) refreshTokenExpirationDays * 24 * 60 * 60 * 1000));
    refreshToken.setRevoked(false);
    return refreshTokenRepository.save(refreshToken);
  }

  @Override
  public Optional<RefreshToken> validateRefreshToken(String token) {
    if (token == null || token.isBlank()) {
      return Optional.empty();
    }
    return refreshTokenRepository
        .findByToken(token)
        .filter(rt -> !rt.isRevoked() && rt.getExpiresAt().after(new Date()));
  }

  @Override
  @Transactional
  public void revokeRefreshToken(String token) {
    refreshTokenRepository
        .findByToken(token)
        .ifPresent(
            rt -> {
              rt.setRevoked(true);
              refreshTokenRepository.save(rt);
            });
  }

  @Override
  @Transactional
  public void revokeAllUserTokens(Long userId) {
    refreshTokenRepository.revokeAllByUserId(userId);
  }

  @Override
  @Transactional
  public long deleteRevokedAndExpiredTokens() {
    int revokedCount = refreshTokenRepository.deleteRevokedTokens();
    refreshTokenRepository.deleteExpiredTokens();
    log.info("Cleaned up {} revoked/expired refresh tokens", revokedCount);
    return revokedCount;
  }

  /**
   * Run cleanup at midnight (00:00) every Saturday. Deletes revoked and expired refresh tokens from
   * DB.
   */
  @Scheduled(cron = "${app.refresh-token.cleanup-cron:0 0 0 ? * SAT}")
  @Transactional
  public void scheduledCleanup() {
    try {
      deleteRevokedAndExpiredTokens();
    } catch (Exception e) {
      log.error("Scheduled refresh token cleanup failed", e);
    }
  }
}
