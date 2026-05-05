package com.pmq.vnnewsvoice.article.repository;

import com.pmq.vnnewsvoice.article.pojo.Generator;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface GeneratorRepository
    extends JpaRepository<Generator, Long>, JpaSpecificationExecutor<Generator> {

  Optional<Generator> findFirstByNameContainingOrUrlContaining(String name, String url);

  long countByIsActiveTrue();

  long countByIsActiveTrueAndNameContaining(String name);

  Optional<Generator> findByNameIgnoreCase(String name);
}
