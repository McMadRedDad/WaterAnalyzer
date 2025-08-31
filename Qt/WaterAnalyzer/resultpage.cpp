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
