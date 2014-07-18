/*
 *    RateProjection.cpp
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
#include "RateProjection.h"
#include "RatePopulation.h"
#include "RateDendrite.h"

#ifdef _DEBUG_PARALLELISM
	#include "ParallelLogger.h"
#endif

RateProjection::RateProjection(): Projection()
{
#ifdef _DEBUG_PARALLELISM
	log_ = new ParallelLogger( omp_get_max_threads(), nbDendrites_ );
#endif
	// register on network
	Network::instance()->addProjection(this, true);
}

RateProjection::~RateProjection()
{
#ifdef _DEBUG
	std::cout << "RateProjection::Destructor" << std::endl;
#endif

#ifdef _DEBUG_PARALLELISM
	if (log_)
		delete log_;
#endif
}

void RateProjection::computeSum()
{
#if defined( _DEBUG ) && defined ( _DEBUG_SIMULATION_CONTROL )
	std::cout << "number of dendrites: " << nbDendrites_ << std::endl;
#endif

	// compute the dendrites in parallel, is equal to a pattern parallel evaluation
	#pragma omp for
	for ( int n = 0; n < nbDendrites_; n++ )
	{
		if (!dendrites_[n])
			continue;

	#ifdef _DEBUG_PARALLELISM
		log_->add(omp_get_thread_num(), n);
	#endif

	#if defined( _DEBUG ) && defined ( _DEBUG_SIMULATION_CONTROL )
		std::cout << "dendrite( ptr = " << dendrites_[n] << ", n = " << n << "): " << dendrites_[n]->getSynapseCount() << " synapse(s) " << std::endl;
	#endif
		static_cast<RateDendrite*>(dendrites_[n])->computeSum();
	}

#ifdef _DEBUG_PARALLELISM
	#pragma omp master
	{
		log_->number_neurons_per_thread( true );
	}
	#pragma omp barrier
#endif
}

void RateProjection::globalLearn()
{
#if defined( _DEBUG ) && defined ( _DEBUG_SIMULATION_CONTROL )
	#pragma omp master
	{
		std::cout << "GlobalLearn: number of dendrites: " << nbDendrites_ << std::endl;
	}
#endif

	if ( ANNarchy_Global::time % learnFrequency_ == learnOffset_ )
	{
		#pragma omp for
		for ( int n = 0; n < nbDendrites_; n++ )
		{
			if (!dendrites_[n])
				continue;

			static_cast<RateDendrite*>(dendrites_[n])->globalLearn();
		}
	}
}

void RateProjection::localLearn()
{
#if defined( _DEBUG ) && defined ( _DEBUG_SIMULATION_CONTROL )
	#pragma omp master
	{
	std::cout << "LocalLearn: number of dendrites: " << nbDendrites_ << std::endl;
	}
#endif

	if ( ANNarchy_Global::time % learnFrequency_ == learnOffset_ )
	{
		#pragma omp for
		for ( int n = 0; n < nbDendrites_; n++ )
		{
			if (!dendrites_[n])
				continue;

			static_cast<RateDendrite*>(dendrites_[n])->localLearn();
		}
	}
}

DATA_TYPE RateProjection::getSum(int neuron)
{
	if ( neuron >= dendrites_.size() )
	{
		std::cout << "No dendrite " << neuron << "on this projection."<< std::endl;
		return 0.0;
	}
	else if  ( !dendrites_[neuron] )
	{
		return 0.0;
	}
	else
	{
		return static_cast<RateDendrite*>(dendrites_[neuron])->getSum();
	}
}

Dendrite *RateProjection::getDendrite(int postNeuronRank)
{
	return dendrites_[postNeuronRank];
}

int RateProjection::nbSynapses(int post_rank) { 
	return dendrites_[post_rank]->getSynapseCount();
}

void RateProjection::removeDendrite(int postNeuronRank, class Population *pre)
{
	std::cout << "Need to implemented in CPP core."<< std::endl;
}


void RateProjection::record()
{
	for ( int n = 0; n < nbDendrites_; n++ )
	{
		if ( !dendrites_[n] )
			continue;

		dendrites_[n]->record();
	}
}

