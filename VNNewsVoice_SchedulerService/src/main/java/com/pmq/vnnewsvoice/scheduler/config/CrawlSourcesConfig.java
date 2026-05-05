package com.pmq.vnnewsvoice.scheduler.config;

import java.util.List;
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Crawl source configuration — loaded from application.properties. Each source represents a news
 * website the Crawling Service will scrape.
 */
@Configuration
@ConfigurationProperties(prefix = "crawl")
@Getter
@Setter
public class CrawlSourcesConfig {

  private List<CrawlSource> sources =
      List.of(
          new CrawlSource("vnexpress", "VnExpress", "https://vnexpress.net"),
          new CrawlSource("tuoitre", "Tuổi Trẻ", "https://tuoitre.vn"),
          new CrawlSource("thanhnien", "Thanh Niên", "https://thanhnien.vn"),
          new CrawlSource("dantri", "Dân Trí", "https://dantri.com.vn"));

  @Getter
  @Setter
  public static class CrawlSource {
    private String id; // sourceId: "vnexpress", "tuoitre", etc.
    private String name; // display name: "VnExpress"
    private String baseUrl; // base URL to crawl from

    public CrawlSource() {}

    public CrawlSource(String id, String name, String baseUrl) {
      this.id = id;
      this.name = name;
      this.baseUrl = baseUrl;
    }
  }
}
