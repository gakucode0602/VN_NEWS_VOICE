package com.pmq.vnnewsvoice.scheduler.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Message payload published to queue "crawl.task". Crawling Service (Phase 1.2) will consume this
 * message and start scraping.
 *
 * <p>Serialized as JSON via Jackson2JsonMessageConverter.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CrawlTaskMessage {

  /** Unique identifier for the news source (e.g. "vnexpress", "tuoitre"). */
  private String sourceId;

  /** Human-readable name (e.g. "VnExpress", "Tuổi Trẻ"). */
  private String sourceName;

  /** Root URL the Crawling Service should scrape (e.g. "https://vnexpress.net"). */
  private String baseUrl;

  /** ISO-8601 timestamp when this task was published (for deduplication/tracing). */
  @JsonFormat(shape = JsonFormat.Shape.STRING)
  private Instant requestedAt;
}
