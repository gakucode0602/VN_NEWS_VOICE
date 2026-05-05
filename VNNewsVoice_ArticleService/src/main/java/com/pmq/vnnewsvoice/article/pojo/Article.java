package com.pmq.vnnewsvoice.article.pojo;

import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import jakarta.persistence.*;
import java.util.Date;
import java.util.Set;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "article")
@Getter
@Setter
@NoArgsConstructor
public class Article {

  @Id
  @Column(name = "id")
  private UUID id;

  @Column(name = "title", nullable = false)
  private String title;

  @Column(name = "author")
  private String author;

  @Column(name = "published_date")
  @Temporal(TemporalType.TIMESTAMP)
  private Date publishedDate;

  @Column(name = "audio_url")
  private String audioUrl;

  @Column(name = "summary")
  private String summary;

  @Column(name = "is_active")
  private Boolean isActive;

  @Column(name = "slug", nullable = false, unique = true)
  private String slug;

  @Column(name = "original_url", unique = true)
  private String originalUrl;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  @Column(name = "updated_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date updatedAt;

  @Column(name = "deleted_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date deletedAt;

  @Column(name = "top_image_url")
  private String topImageUrl;

  @Column(name = "video_url", length = 500)
  private String videoUrl;

  @Column(name = "is_video_accepted")
  private Boolean isVideoAccepted = false;

  @Enumerated(EnumType.STRING)
  @Column(name = "status")
  private ArticleStatus status;

  @JoinColumn(name = "category_id", referencedColumnName = "id")
  @ManyToOne
  private Category categoryId;

  @JoinColumn(name = "generator_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private Generator generatorId;

  @OneToMany(
      cascade = {CascadeType.MERGE, CascadeType.REFRESH},
      mappedBy = "articleId")
  private Set<ArticleBlock> articleblockSet;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "articleId")
  private Set<ArticleLike> articleLikeSet;

  public Article(UUID id) {
    this.id = id;
  }

  public Article(UUID id, String title, String slug) {
    this.id = id;
    this.title = title;
    this.slug = slug;
  }
}
