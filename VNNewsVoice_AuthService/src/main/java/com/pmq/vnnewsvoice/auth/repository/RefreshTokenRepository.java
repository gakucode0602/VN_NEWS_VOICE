package com.pmq.vnnewsvoice.auth.repository;

import com.pmq.vnnewsvoice.auth.pojo.RefreshToken;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

  Optional<RefreshToken> findByToken(String token);

  @Modifying
  @Query(
      "UPDATE RefreshToken r SET r.revoked = true WHERE r.userId.id = :userId AND r.revoked = false")
  void revokeAllByUserId(@Param("userId") Long userId);

  @Modifying
  @Query("DELETE FROM RefreshToken r WHERE r.expiresAt < CURRENT_TIMESTAMP")
  void deleteExpiredTokens();

  @Modifying
  @Query("DELETE FROM RefreshToken r WHERE r.revoked = true")
  int deleteRevokedTokens();
}
