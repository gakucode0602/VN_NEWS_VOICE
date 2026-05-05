package com.pmq.vnnewsvoice.article.pojo;

import jakarta.persistence.*;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "category")
@Getter
@Setter
@NoArgsConstructor
public class Category {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "name", nullable = false, unique = true)
  private String name;

  @Column(name = "description")
  private String description;

  @Column(name = "is_active")
  private Boolean isActive;

  @OneToMany(mappedBy = "categoryId")
  private Set<Article> articleSet;

  public Category(Long id) {
    this.id = id;
  }

  public Category(Long id, String name) {
    this.id = id;
    this.name = name;
  }
}
