#include "resultpage.hpp"
#include "ui_resultpage.h"

ResultPage::ResultPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ResultPage) {
  ui->setupUi(this);
  summary = new ResultTab();
  water = new ResultTab();
  chloro = new ResultTab();
  tss = new ResultTab();
  cdom = new ResultTab();
  temp = new ResultTab();
  ui->tab_summary->layout()->addWidget(summary);
  ui->tab_water->layout()->addWidget(water);
  ui->tab_chloro->layout()->addWidget(chloro);
  ui->tab_tss->layout()->addWidget(tss);
  ui->tab_cdom->layout()->addWidget(cdom);
  ui->tab_temp->layout()->addWidget(temp);
  summary->set_caption("Итог");
}

ResultPage::~ResultPage() {
  delete ui;
  delete summary;
  delete water;
  delete chloro;
  delete tss;
  delete cdom;
  delete temp;
}

void ResultPage::set_preview(QString page, QPixmap image) {
  if (page == "summary") {
    summary->set_preview(image);
  } else if (page == "water") {
    water->set_preview(image);
  } else if (page == "chloro") {
    chloro->set_preview(image);
  } else if (page == "tss") {
    tss->set_preview(image);
  } else if (page == "cdom") {
    cdom->set_preview(image);
  } else if (page == "temp") {
    temp->set_preview(image);
  }
}

uint ResultPage::get_preview_width() { return summary->get_preview_width(); }

uint ResultPage::get_preview_height() { return summary->get_preview_height(); }

void ResultPage::set_caption(QString page, QString caption) {
  if (page == "summary") {
    summary->set_caption(caption);
  } else if (page == "water") {
    water->set_caption(caption);
  } else if (page == "chloro") {
    chloro->set_caption(caption);
  } else if (page == "tss") {
    tss->set_caption(caption);
  } else if (page == "cdom") {
    cdom->set_caption(caption);
  } else if (page == "temp") {
    temp->set_caption(caption);
  }
}
