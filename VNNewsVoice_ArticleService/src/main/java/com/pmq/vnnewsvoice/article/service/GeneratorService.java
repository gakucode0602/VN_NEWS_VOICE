package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.pojo.Generator;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface GeneratorService {
  Generator addGenerator(Generator generator);

  Optional<Generator> getGeneratorById(Long id);

  Optional<Generator> getGeneratorByName(String name);

  String getGeneratorURL(Long id);

  List<Generator> getGenerators(Map<String, String> params);

  Optional<Generator> updateGenerator(Generator generator);

  boolean deleteGenerator(Long id);

  long countGenerators();

  long countSearchGenerators(Map<String, String> filters);

  long countActiveGenerators(Map<String, String> params);

  LocalDateTime getLastCrawlTimeOfGeneratorByGenerator(Generator generator);

  LocalDateTime getLastCrawlTimeOfGeneratorById(Long id);

  LocalDateTime getLastCrawlTimeOfGeneratorByName(String name);

  boolean isValidGenerator(Generator generator);
}
