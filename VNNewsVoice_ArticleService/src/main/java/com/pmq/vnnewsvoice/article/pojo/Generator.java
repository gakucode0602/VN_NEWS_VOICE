package com.pmq.vnnewsvoice.article.pojo;

import jakarta.persistence.*;
import java.util.Date;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "generator")
@Getter
@Setter
@NoArgsConstructor
public class Generator {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "name", nullable = false, unique = true)
  private String name;

  @Column(name = "logo_url")
  private String logoUrl;

  @Column(name = "url", nullable = false, unique = true)
  private String url;

  @Column(name = "last_time_crawled")
  @Temporal(TemporalType.TIMESTAMP)
  private Date lastTimeCrawled;

  @Column(name = "rss_url")
  private String rssUrl;

  @Column(name = "is_active")
  private Boolean isActive;

  @Column(name = "crawl_interval_minutes")
  private Integer crawlIntervalMinutes;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "generatorId")
  private Set<Article> articleSet;

  public Generator(Long id) {
    this.id = id;
  }

  public Generator(Long id, String name, String url) {
    this.id = id;
    this.name = name;
    this.url = url;
  }
}
