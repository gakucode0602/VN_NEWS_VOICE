package com.pmq.vnnewsvoice.scheduler.scheduler;

import com.pmq.vnnewsvoice.scheduler.config.CrawlSourcesConfig;
import com.pmq.vnnewsvoice.scheduler.service.CrawlPublisherService;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Scheduled job — triggers crawl tasks at a configurable interval.
 *
 * <p>On each trigger, publishes one CrawlTaskMessage per source to queue "crawl.task". Crawling
 * Service (Phase 1.2) consumes these messages and performs the actual crawling.
 *
 * <p>Schedule is configurable via fixedDelay/initialDelay properties to mirror legacy behavior: -
 * Default fixed delay: 4 hours (14,400,000 ms) - Default initial delay: 10 minutes (600,000 ms)
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class CrawlScheduler {

  private final CrawlPublisherService crawlPublisherService;
  private final CrawlSourcesConfig crawlSourcesConfig;

  @Value("${crawler.scheduling.enabled:true}")
  private boolean schedulingEnabled;

  /**
   * Publishes crawl tasks for all configured sources. Cron is externalized — can override without
   * code change.
   */
  @Scheduled(
      fixedDelayString = "${crawl.schedule.fixed-delay-ms}",
      initialDelayString = "${crawl.schedule.initial-delay-ms}")
  public void scheduleCrawlTasks() {
    if (!schedulingEnabled) {
      log.info("Crawl scheduling is disabled by property crawler.scheduling.enabled=false");
      return;
    }

    log.info("=== CrawlScheduler triggered at {} ===", LocalDateTime.now());

    var sources = crawlSourcesConfig.getSources();
    if (sources == null || sources.isEmpty()) {
      log.warn("No crawl sources configured — skipping scheduled crawl");
      return;
    }

    log.info("Publishing crawl tasks for {} sources...", sources.size());
    for (CrawlSourcesConfig.CrawlSource source : sources) {
      try {
        crawlPublisherService.publishCrawlTask(source);
      } catch (Exception e) {
        // Continue publishing other sources even if one fails
        log.error("Failed to publish crawl task for source={}: {}", source.getId(), e.getMessage());
      }
    }

    log.info("=== CrawlScheduler done — {} tasks published ===", sources.size());
  }
}
