package com.pmq.vnnewsvoice.article.pojo;

import jakarta.persistence.*;
import java.util.Date;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "articlelike")
@Getter
@Setter
@NoArgsConstructor
public class ArticleLike {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  @JoinColumn(name = "article_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private Article articleId;

  // reader_id stores UserInfo.id (from JWT claims) — no FK to auth_db Reader entity
  @Column(name = "reader_id", nullable = false)
  private Long readerId;

  public ArticleLike(Long id) {
    this.id = id;
  }
}
