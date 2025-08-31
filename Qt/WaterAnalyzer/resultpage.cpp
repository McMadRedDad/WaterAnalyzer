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

void ResultPage::set_summary_preview(QPixmap image) {
  summary->set_preview(image);
}

void ResultPage::set_water_preview(QPixmap image) { water->set_preview(image); }

void ResultPage::set_chloro_preview(QPixmap image) {
  chloro->set_preview(image);
}

void ResultPage::set_tss_preview(QPixmap image) { tss->set_preview(image); }

void ResultPage::set_cdom_preview(QPixmap image) { cdom->set_preview(image); }

void ResultPage::set_temp_preview(QPixmap image) { temp->set_preview(image); }

uint ResultPage::get_preview_width() { return summary->get_preview_width(); }

uint ResultPage::get_preview_height() { return summary->get_preview_height(); }
