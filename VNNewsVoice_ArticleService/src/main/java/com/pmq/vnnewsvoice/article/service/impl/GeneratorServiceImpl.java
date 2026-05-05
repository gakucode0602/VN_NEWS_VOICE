package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.pojo.Generator;
import com.pmq.vnnewsvoice.article.repository.GeneratorRepository;
import com.pmq.vnnewsvoice.article.repository.RepositoryPageable;
import com.pmq.vnnewsvoice.article.repository.specification.GeneratorSpecifications;
import com.pmq.vnnewsvoice.article.service.GeneratorService;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class GeneratorServiceImpl implements GeneratorService {
  private final GeneratorRepository generatorRepository;

  @Override
  @Transactional
  public Generator addGenerator(Generator generator) {
    if (isValidGenerator(generator)) {
      return generatorRepository.save(generator);
    }
    return null;
  }

  @Override
  public Optional<Generator> getGeneratorById(Long id) {
    if (id == null) {
      return Optional.empty();
    }
    return generatorRepository.findById(id);
  }

  @Override
  public Optional<Generator> getGeneratorByName(String name) {
    if (name == null || name.isEmpty()) {
      return Optional.empty();
    }
    return generatorRepository.findFirstByNameContainingOrUrlContaining(name, name);
  }

  @Override
  public String getGeneratorURL(Long id) {
    Optional<Generator> generatorOptional = generatorRepository.findById(id);
    if (generatorOptional.isEmpty()) {
      return "";
    }
    return generatorOptional.get().getUrl();
  }

  @Override
  public List<Generator> getGenerators(Map<String, String> params) {
    if (params == null || params.isEmpty()) {
      return generatorRepository.findAll();
    }
    Specification<Generator> spec = GeneratorSpecifications.fromFilters(params);
    return RepositoryPageable.fromParams(params, 10, Sort.unsorted())
        .map(pageable -> generatorRepository.findAll(spec, pageable).getContent())
        .orElse(generatorRepository.findAll(spec));
  }

  @Override
  @Transactional
  public Optional<Generator> updateGenerator(Generator generator) {
    if (isValidGenerator(generator)
        && generator.getId() != null
        && generatorRepository.existsById(generator.getId())) {
      return Optional.of(generatorRepository.save(generator));
    }
    return Optional.empty();
  }

  @Override
  @Transactional
  public boolean deleteGenerator(Long id) {
    if (id == null || !generatorRepository.existsById(id)) {
      return false;
    }
    generatorRepository.deleteById(id);
    return true;
  }

  @Override
  public long countGenerators() {
    return generatorRepository.count();
  }

  @Override
  public long countSearchGenerators(Map<String, String> filters) {
    if (filters == null || filters.isEmpty()) {
      return generatorRepository.count();
    }
    Specification<Generator> spec = GeneratorSpecifications.fromFilters(filters);
    return generatorRepository.count(spec);
  }

  @Override
  public long countActiveGenerators(Map<String, String> params) {
    if (params == null || params.isEmpty()) {
      return generatorRepository.countByIsActiveTrue();
    }
    String name = params.getOrDefault("name", "");
    if (!name.isEmpty()) {
      return generatorRepository.countByIsActiveTrueAndNameContaining(name);
    }
    return generatorRepository.countByIsActiveTrue();
  }

  @Override
  public LocalDateTime getLastCrawlTimeOfGeneratorByGenerator(Generator generator) {
    if (isValidGenerator(generator) && generator.getId() != null) {
      return generatorRepository
          .findById(generator.getId())
          .map(
              g -> {
                Date lastCrawl = g.getLastTimeCrawled();
                return lastCrawl != null
                    ? lastCrawl.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime()
                    : null;
              })
          .orElse(null);
    }
    return null;
  }

  @Override
  public LocalDateTime getLastCrawlTimeOfGeneratorById(Long id) {
    if (id == null || id <= 0) {
      return null;
    }
    return generatorRepository
        .findById(id)
        .map(
            g -> {
              Date lastCrawl = g.getLastTimeCrawled();
              return lastCrawl != null
                  ? lastCrawl.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime()
                  : null;
            })
        .orElse(null);
  }

  @Override
  public LocalDateTime getLastCrawlTimeOfGeneratorByName(String name) {
    if (name == null || name.isEmpty()) {
      return null;
    }
    return generatorRepository
        .findFirstByNameContainingOrUrlContaining(name, name)
        .map(
            g -> {
              Date lastCrawl = g.getLastTimeCrawled();
              return lastCrawl != null
                  ? lastCrawl.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime()
                  : null;
            })
        .orElse(null);
  }

  @Override
  public boolean isValidGenerator(Generator generator) {
    if (generator == null) {
      return false;
    }
    if (generator.getId() != null) {
      Optional<Generator> existing = generatorRepository.findById(generator.getId());
      if (existing.isEmpty()) {
        return false;
      }
    }
    if (generator.getName() == null
        || generator.getName().isEmpty()
        || generator.getUrl() == null
        || generator.getUrl().isEmpty()) {
      return false;
    }
    return true;
  }
}
