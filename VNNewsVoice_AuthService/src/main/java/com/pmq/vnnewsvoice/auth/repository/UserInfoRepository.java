package com.pmq.vnnewsvoice.auth.repository;

import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface UserInfoRepository
    extends JpaRepository<UserInfo, Long>, JpaSpecificationExecutor<UserInfo> {

  Optional<UserInfo> findFirstByUsername(String username);

  Optional<UserInfo> findFirstByEmail(String email);

  @Override
  @EntityGraph(attributePaths = "roleId")
  Page<UserInfo> findAll(Specification<UserInfo> spec, Pageable pageable);
}
