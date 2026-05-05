package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage;
import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage.BlockMessage;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import com.pmq.vnnewsvoice.article.pojo.Generator;
import com.pmq.vnnewsvoice.article.repository.ArticleBlockRepository;
import com.pmq.vnnewsvoice.article.repository.ArticleRepository;
import com.pmq.vnnewsvoice.article.repository.GeneratorRepository;
import java.text.Normalizer;
import java.time.Instant;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Handles incoming ArticleEventMessage from fanout queue 'article.events.article-service'.
 *
 * <p>Idempotent upsert strategy:
 *
 * <ul>
 *   <li>Find existing article by {@code originalUrl} (unique constraint)
 *   <li>If found: update summary + audioUrl + topImage (fields enriched by MLService)
 *   <li>If not found: create new article + blocks
 * </ul>
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ArticleEventService {

  private final ArticleRepository articleRepository;
  private final ArticleBlockRepository articleBlockRepository;
  private final GeneratorRepository generatorRepository;

  @Transactional
  public void handleArticleCreated(ArticleEventMessage event) {
    if (event.getUrl() == null || event.getTitle() == null) {
      log.warn("[AMQP] Skipping invalid article event: missing url or title");
      return;
    }

    Optional<Article> existing = articleRepository.findByOriginalUrl(event.getUrl());
    if (existing.isPresent()) {
      updateArticle(existing.get(), event);
    } else {
      createArticle(event);
    }
  }

  @Transactional
  public void handleVideoGenerated(ArticleEventMessage event) {
    if (event.getArticleId() == null || event.getVideoUrl() == null) {
      log.warn("[AMQP] Skipping video.generated: missing articleId or videoUrl");
      return;
    }
    Optional<Article> articleOpt = articleRepository.findById(event.getArticleId());
    if (articleOpt.isEmpty()) {
      log.warn("[AMQP] video.generated: article not found id={}", event.getArticleId());
      return;
    }
    Article article = articleOpt.get();
    article.setVideoUrl(event.getVideoUrl());
    article.setIsVideoAccepted(false);
    article.setUpdatedAt(new Date());
    articleRepository.save(article);
    log.info("[AMQP] Saved videoUrl for articleId={} url={}", article.getId(), event.getVideoUrl());
  }

  private void createArticle(ArticleEventMessage event) {
    Article article = new Article();
    article.setId(event.getArticleId());
    article.setTitle(event.getTitle());
    article.setOriginalUrl(event.getUrl());
    article.setTopImageUrl(event.getTopImage());
    article.setSummary(event.getSummary());
    article.setAudioUrl(event.getAudioUrl());
    article.setIsActive(true);
    article.setStatus(ArticleStatus.PUBLISHED);
    article.setSlug(generateSlug(event.getTitle()));
    article.setCreatedAt(new Date());
    article.setUpdatedAt(new Date());

    if (event.getPublishedAt() != null) {
      try {
        article.setPublishedDate(Date.from(Instant.parse(event.getPublishedAt())));
      } catch (Exception e) {
        article.setPublishedDate(new Date());
      }
    } else {
      article.setPublishedDate(new Date());
    }

    // Resolve generator by sourceId (e.g. "vnexpress" → Generator row)
    Generator generator =
        resolveGenerator(event.getSourceId(), event.getSourceName(), event.getUrl());
    article.setGeneratorId(generator);

    Article saved = articleRepository.save(article);
    log.info("[AMQP] Created article id={} url={}", saved.getId(), saved.getOriginalUrl());

    // Persist blocks
    if (event.getBlocks() != null && !event.getBlocks().isEmpty()) {
      saveBlocks(event.getBlocks(), saved);
    }
  }

  private void updateArticle(Article article, ArticleEventMessage event) {
    article.setSummary(event.getSummary());
    article.setAudioUrl(event.getAudioUrl());
    if (event.getTopImage() != null && !event.getTopImage().isBlank()) {
      article.setTopImageUrl(event.getTopImage());
    }
    article.setUpdatedAt(new Date());
    articleRepository.save(article);
    log.info("[AMQP] Updated article id={} url={}", article.getId(), article.getOriginalUrl());
  }

  private void saveBlocks(List<BlockMessage> blockMessages, Article article) {
    // Delete old blocks first (idempotent for re-processing)
    articleBlockRepository.deleteByArticleId(article);

    List<ArticleBlock> blocks =
        blockMessages.stream()
            .map(
                b -> {
                  ArticleBlock block = new ArticleBlock();
                  block.setOrderIndex(b.getOrder());
                  block.setType(b.getType());
                  block.setContent(b.getContent());
                  block.setText(b.getText());
                  block.setTag(b.getTag());
                  block.setSrc(b.getSrc());
                  block.setAlt(b.getAlt());
                  block.setCaption(b.getCaption());
                  block.setArticleId(article);
                  return block;
                })
            .toList();

    articleBlockRepository.saveAll(blocks);
    log.info("[AMQP] Saved {} blocks for article id={}", blocks.size(), article.getId());
  }

  private Generator resolveGenerator(String sourceId, String sourceName, String articleUrl) {
    // Try to find by name (case-insensitive) or fall back to first active generator
    return generatorRepository
        .findByNameIgnoreCase(sourceName)
        .or(() -> generatorRepository.findByNameIgnoreCase(sourceId))
        .orElseGet(
            () -> {
              // Auto-create generator if not found
              Generator g = new Generator();
              g.setName(sourceName != null ? sourceName : sourceId);
              g.setUrl(extractBaseUrl(articleUrl));
              g.setIsActive(true);
              g.setLastTimeCrawled(new Date());
              Generator saved = generatorRepository.save(g);
              log.info("[AMQP] Auto-created generator '{}' id={}", saved.getName(), saved.getId());
              return saved;
            });
  }

  private static String extractBaseUrl(String url) {
    if (url == null) return "";
    try {
      java.net.URI uri = java.net.URI.create(url);
      return uri.getScheme() + "://" + uri.getHost();
    } catch (Exception e) {
      return url;
    }
  }

  private static String generateSlug(String title) {
    if (title == null) return String.valueOf(System.currentTimeMillis());
    String normalized = Normalizer.normalize(title, Normalizer.Form.NFD);
    String ascii =
        Pattern.compile("\\p{InCombiningDiacriticalMarks}+").matcher(normalized).replaceAll("");
    String slug =
        ascii
            .toLowerCase(Locale.ROOT)
            .replaceAll("[^a-z0-9\\s-]", "")
            .replaceAll("\\s+", "-")
            .replaceAll("-+", "-")
            .replaceAll("^-|-$", "");
    // append timestamp to ensure uniqueness
    return slug.substring(0, Math.min(slug.length(), 100)) + "-" + System.currentTimeMillis();
  }
}
