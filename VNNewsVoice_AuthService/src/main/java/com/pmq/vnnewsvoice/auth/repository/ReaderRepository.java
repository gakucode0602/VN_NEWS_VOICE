package com.pmq.vnnewsvoice.auth.repository;

import com.pmq.vnnewsvoice.auth.pojo.Reader;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;

public interface ReaderRepository
    extends JpaRepository<Reader, Long>, JpaSpecificationExecutor<Reader> {

  Optional<Reader> findFirstByUserId_Username(String username);

  Optional<Reader> findFirstByUserId_Email(String email);

  Optional<Reader> findFirstByUserId_Id(Long userId);

  @Query(
      "SELECT r FROM Reader r JOIN r.userId u JOIN u.userProviderSet up WHERE up.id = :providerId")
  Optional<Reader> findFirstByUserProviderId(Long providerId);
}
