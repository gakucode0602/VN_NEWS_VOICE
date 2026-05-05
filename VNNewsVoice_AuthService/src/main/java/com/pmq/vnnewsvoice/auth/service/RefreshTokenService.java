package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.RefreshToken;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import java.util.Optional;

public interface RefreshTokenService {

  RefreshToken createRefreshToken(UserInfo userInfo);

  Optional<RefreshToken> validateRefreshToken(String token);

  void revokeRefreshToken(String token);

  void revokeAllUserTokens(Long userId);

  long deleteRevokedAndExpiredTokens();
}
