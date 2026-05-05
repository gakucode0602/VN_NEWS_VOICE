package com.pmq.vnnewsvoice.article.pojo;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "articleblock")
@Getter
@Setter
@NoArgsConstructor
public class ArticleBlock {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "order_index", nullable = false)
  private int orderIndex;

  @Column(name = "type", nullable = false)
  private String type;

  @Column(name = "content")
  private String content;

  @Column(name = "text")
  private String text;

  @Column(name = "tag")
  private String tag;

  @Column(name = "src")
  private String src;

  @Column(name = "alt")
  private String alt;

  @Column(name = "caption")
  private String caption;

  @JoinColumn(name = "article_id", referencedColumnName = "id")
  @ManyToOne
  private Article articleId;

  public ArticleBlock(Long id) {
    this.id = id;
  }
}
