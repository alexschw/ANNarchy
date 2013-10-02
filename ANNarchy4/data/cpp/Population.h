/*
 *    Population.h
 *
 *    This file is part of ANNarchy.
 *   
 *   Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
 *   Helge Ülo Dinkelbach <helge.dinkelbach@gmail.com>
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   ANNarchy is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef __POPULATION_H__
#define __POPULATION_H__

#include "Global.h"

class Population{
public:
	// functions
	Population(std::string name, int nbNeurons);

	virtual ~Population();

	virtual void metaSum();
	virtual void metaStep();
	virtual void metaLearn();
	virtual void globalOperations();

	std::string getName() { return name_; }

	virtual int getNeuronCount() { return nbNeurons_; }

	class Projection* getProjection(int neuron, int type) { return projections_[neuron][type]; }

	void addProjection(int postRankID, Projection* proj);

	void removeProjection(Population *pre);

	void printRates();

	void setMaxDelay(int delay);

	DATA_TYPE sum(int neur, int type);

	std::vector<DATA_TYPE>* getRates() {
		return &rate_;
	}

	std::vector<DATA_TYPE>* getRates(int delay) {
		if (delay < (int)delayedRates_.size())
			return &(delayedRates_[delay-1]);
		else
			return NULL;
	}

	std::vector<DATA_TYPE> getRates(std::vector<int> delays, std::vector<int> ranks);

	DATA_TYPE getDt() { return dt_;	}

	void setDt(DATA_TYPE dt) { dt_ = dt; }
#ifdef ANNAR_PROFILE
    FILE *cs;
    FILE *gl;
    FILE *ll;
#endif
protected:
	// data
	int nbNeurons_;
	std::string name_;	///< name of layer
	int maxDelay_;
	DATA_TYPE dt_;

	std::vector<DATA_TYPE>	rate_;
	std::vector< std::vector<DATA_TYPE>	> delayedRates_;
	std::vector<std::vector<class Projection*> > projections_;	// first dimension, neuron wise
};

#endif
