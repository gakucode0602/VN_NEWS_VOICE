package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.dto.ArticleClaimRequest;
import com.pmq.vnnewsvoice.article.dto.ArticleClaimResponse;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.repository.ArticleRepository;
import java.net.URI;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class ArticleClaimService {

  private static final Set<String> DROP_QUERY_PARAMS =
      Set.of("fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "spm");

  private final ArticleRepository articleRepository;

  @Transactional(readOnly = true)
  public ArticleClaimResponse claim(ArticleClaimRequest request) {
    String canonicalUrl = canonicalizeUrl(request.getUrl());
    if (canonicalUrl.isBlank()) {
      return ArticleClaimResponse.builder()
          .shouldProcess(false)
          .reason("invalid_url")
          .canonicalUrl("")
          .build();
    }

    Optional<Article> existing = articleRepository.findByOriginalUrl(canonicalUrl);
    if (existing.isPresent()) {
      String articleId = existing.get().getId() != null ? existing.get().getId().toString() : null;
      log.info("[CLAIM] Duplicate article rejected: url={} articleId={}", canonicalUrl, articleId);
      return ArticleClaimResponse.builder()
          .shouldProcess(false)
          .reason("duplicate_original_url")
          .canonicalUrl(canonicalUrl)
          .matchedArticleId(articleId)
          .build();
    }

    return ArticleClaimResponse.builder()
        .shouldProcess(true)
        .reason("new_article")
        .canonicalUrl(canonicalUrl)
        .build();
  }

  private static String canonicalizeUrl(String rawUrl) {
    if (rawUrl == null) return "";
    String trimmed = rawUrl.trim();
    if (trimmed.isEmpty()) return "";

    try {
      URI uri = URI.create(trimmed);

      String scheme = uri.getScheme() != null ? uri.getScheme().toLowerCase(Locale.ROOT) : "https";
      String host = uri.getHost() != null ? uri.getHost().toLowerCase(Locale.ROOT) : "";
      int port = uri.getPort();

      String authority = host;
      boolean isDefaultPort =
          port == -1
              || ("http".equals(scheme) && port == 80)
              || ("https".equals(scheme) && port == 443);
      if (!isDefaultPort && port > 0 && !host.isBlank()) {
        authority = host + ":" + port;
      }

      String path = uri.getPath();
      if (path == null || path.isBlank()) {
        path = "/";
      } else if (path.length() > 1 && path.endsWith("/")) {
        path = path.substring(0, path.length() - 1);
      }

      String query = normalizeQuery(uri.getRawQuery());
      URI normalized = new URI(scheme, authority, path, query, null);
      return normalized.toASCIIString();
    } catch (Exception e) {
      return trimmed;
    }
  }

  private static String normalizeQuery(String rawQuery) {
    if (rawQuery == null || rawQuery.isBlank()) {
      return null;
    }

    List<String> filteredParts =
        Arrays.stream(rawQuery.split("&"))
            .map(String::trim)
            .filter(part -> !part.isBlank())
            .filter(
                part -> {
                  String key = part.split("=", 2)[0].toLowerCase(Locale.ROOT);
                  return !key.startsWith("utm_") && !DROP_QUERY_PARAMS.contains(key);
                })
            .toList();

    if (filteredParts.isEmpty()) {
      return null;
    }

    return String.join("&", filteredParts);
  }
}
