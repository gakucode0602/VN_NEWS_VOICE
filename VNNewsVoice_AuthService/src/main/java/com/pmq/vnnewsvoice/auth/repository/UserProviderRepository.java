package com.pmq.vnnewsvoice.auth.repository;

import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserProviderRepository extends JpaRepository<UserProvider, Long> {
  List<UserProvider> findByUserId_Id(Long userId);

  Optional<UserProvider> findFirstByProviderIdAndProviderType(
      String providerId, String providerType);

  boolean existsByUserId_IdAndProviderType(Long userId, String providerType);

  long deleteByUserId_Id(Long userId);
}
